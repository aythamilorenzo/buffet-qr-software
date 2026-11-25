"""Use case that activates a table session for a waiter-declared guest count."""

from datetime import datetime

from app.domain.exceptions import (
    MaxDinersPerTableExceededError,
    TableSessionAlreadyActiveError,
)
from app.domain.restaurant_policy import RestaurantPolicy
from app.domain.table_session import TableSession
from app.ports.session_repository import SessionRepositoryPort


class OpenTableSessionUseCase:
    """Activates a table after enforcing the restaurant seat cap and table state.

    The declared guest count is validated against the per-restaurant policy
    instead of a hardcoded constant, and a table that already runs an open
    session is rejected so two sessions never overlap on the same table.
    """

    def __init__(
        self,
        session_repository: SessionRepositoryPort,
        policy: RestaurantPolicy,
    ) -> None:
        self._session_repository = session_repository
        self._policy = policy

    async def execute(
        self,
        table_number: str,
        guest_count: int,
        opened_at: datetime,
    ) -> TableSession:
        if guest_count > self._policy.max_diners_per_table:
            raise MaxDinersPerTableExceededError(
                f"Table {table_number} declared {guest_count} diners but the "
                f"restaurant allows at most "
                f"{self._policy.max_diners_per_table} per table."
            )
        active_session = await self._session_repository.get_active_by_table(
            table_number,
        )
        if active_session is not None:
            raise TableSessionAlreadyActiveError(
                f"Table {table_number} already runs session "
                f"{active_session.session_id}."
            )
        session = TableSession(
            table_number=table_number,
            guest_count=guest_count,
            opened_at=opened_at,
        )
        await self._session_repository.save(session)
        return session
