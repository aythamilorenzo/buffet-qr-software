"""Use case that removes one dish line from the shared cart of a session."""

from uuid import UUID

from app.domain.exceptions import (
    SessionNotActiveError,
    TableSessionNotFoundError,
)
from app.ports.order_repository import OrderRepositoryPort
from app.ports.session_repository import SessionRepositoryPort


class RemoveCartItemUseCase:
    """Drops one pending cart line while its table session is still open.

    Removal is idempotent: deleting a line that is already gone succeeds
    silently so concurrent edits by several diners converge without errors.
    """

    def __init__(
        self,
        session_repository: SessionRepositoryPort,
        order_repository: OrderRepositoryPort,
    ) -> None:
        self._session_repository = session_repository
        self._order_repository = order_repository

    async def execute(self, session_id: UUID, item_id: UUID) -> None:
        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise TableSessionNotFoundError(
                f"Table session {session_id} does not exist."
            )
        if not session.is_open:
            raise SessionNotActiveError(
                f"Session {session_id} is closed and its cart is frozen."
            )
        await self._order_repository.remove_cart_item(session_id, item_id)
