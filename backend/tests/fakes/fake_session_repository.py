"""In-memory fake of SessionRepositoryPort for use case tests."""

from uuid import UUID

from app.domain.table_session import TableSession
from app.ports.session_repository import SessionRepositoryPort


class FakeSessionRepository(SessionRepositoryPort):
    """Stores sessions in a dictionary to run use cases without PostgreSQL."""

    def __init__(self) -> None:
        self._sessions: dict[UUID, TableSession] = {}

    async def get_by_id(self, session_id: UUID) -> TableSession | None:
        return self._sessions.get(session_id)

    async def get_active_by_table(self, table_number: str) -> TableSession | None:
        return next(
            (
                session
                for session in self._sessions.values()
                if session.table_number == table_number and session.is_open
            ),
            None,
        )

    async def list_active(self) -> list[TableSession]:
        return [
            session
            for session in self._sessions.values()
            if session.is_open
        ]

    async def save(self, session: TableSession) -> None:
        self._sessions[session.session_id] = session
