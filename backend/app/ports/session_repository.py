"""Port for persisting and querying table sessions."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.table_session import TableSession


class SessionRepositoryPort(ABC):
    """Contract the application layer uses to read and write table sessions.

    Implementations must run each application request inside a single
    transaction and lock the session row (`SELECT ... FOR UPDATE`) on every
    read that precedes a domain mutation, so concurrent diner assignments and
    round submissions serialize instead of losing updates.
    """

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> TableSession | None:
        """Returns the session with the given identifier, or None if unknown."""

    @abstractmethod
    async def get_active_by_table(self, table_number: str) -> TableSession | None:
        """Returns the currently open session of a physical table, or None."""

    @abstractmethod
    async def list_active(self) -> list[TableSession]:
        """Returns every open session for the waiter panel."""

    @abstractmethod
    async def save(self, session: TableSession) -> None:
        """Inserts or updates the session state as one atomic write."""
