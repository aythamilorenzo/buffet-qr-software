"""Use case that seats the next diner identifier at an open table session."""

from uuid import UUID

from app.domain.exceptions import TableSessionNotFoundError
from app.domain.table_session import TableSession
from app.domain.value_objects import DinerIdentifier
from app.ports.session_repository import SessionRepositoryPort


class AssignDinerIdentifierUseCase:
    """Assigns the next sequential letter (A, B, C...) to a joining diner.

    The letter is computed by the domain against the session guest count, and
    the updated session is persisted so every concurrent join observes the
    next free identifier instead of reusing one.
    """

    def __init__(self, session_repository: SessionRepositoryPort) -> None:
        self._session_repository = session_repository

    async def execute(
        self,
        session_id: UUID,
    ) -> tuple[TableSession, DinerIdentifier]:
        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise TableSessionNotFoundError(
                f"Table session {session_id} does not exist."
            )
        updated_session, identifier = session.assign_next_identifier()
        await self._session_repository.save(updated_session)
        return updated_session, identifier
