"""Use case that closes an open table session."""

from datetime import datetime
from uuid import UUID

from app.domain.exceptions import TableSessionNotFoundError
from app.domain.table_session import TableSession
from app.ports.session_repository import SessionRepositoryPort


class CloseTableSessionUseCase:
    """Stops the ordering flow of a table by closing its active session.

    Closing is rejected by the domain when the session is already closed, so
    concurrent waiter clicks converge on a single valid transition.
    """

    def __init__(self, session_repository: SessionRepositoryPort) -> None:
        self._session_repository = session_repository

    async def execute(self, session_id: UUID, closed_at: datetime) -> TableSession:
        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise TableSessionNotFoundError(
                f"Table session {session_id} does not exist."
            )
        closed_session = session.close(closed_at)
        await self._session_repository.save(closed_session)
        return closed_session
