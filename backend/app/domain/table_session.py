"""TableSession entity: the live ordering context shared by diners at one table."""

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from app.domain.exceptions import (
    GuestCapacityExceededError,
    InvalidDomainValueError,
    SessionNotActiveError,
)
from app.domain.value_objects import MAX_DINER_IDENTIFIERS, DinerIdentifier


class SessionStatus(StrEnum):
    """Lifecycle states of a table session."""

    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True, kw_only=True)
class TableSession:
    """Shared ordering context of one activated table, immutable by design.

    Every transition (assigning the next diner, closing the session) returns a
    new instance so concurrent readers never observe partially updated state.
    Diner identifiers are assigned sequentially up to the guest count declared
    by the waiter when the table was activated.
    """

    session_id: UUID = field(default_factory=uuid4)
    table_number: str
    guest_count: int
    opened_at: datetime
    status: SessionStatus = SessionStatus.OPEN
    assigned_identifiers: tuple[DinerIdentifier, ...] = ()
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.table_number.strip():
            raise InvalidDomainValueError("table_number must not be empty.")
        if not 1 <= self.guest_count <= MAX_DINER_IDENTIFIERS:
            raise InvalidDomainValueError(
                f"guest_count must be between 1 and {MAX_DINER_IDENTIFIERS}, "
                f"got {self.guest_count}."
            )
        if len(self.assigned_identifiers) > self.guest_count:
            raise InvalidDomainValueError(
                "A session cannot hold more diner identifiers than its guest count."
            )
        if self.status is SessionStatus.CLOSED and self.closed_at is None:
            raise InvalidDomainValueError(
                "A closed session requires a closed_at timestamp."
            )
        if self.status is SessionStatus.OPEN and self.closed_at is not None:
            raise InvalidDomainValueError(
                "An open session must not carry a closed_at timestamp."
            )

    @property
    def is_open(self) -> bool:
        return self.status is SessionStatus.OPEN

    def assign_next_identifier(self) -> tuple["TableSession", DinerIdentifier]:
        """Assigns the next sequential diner letter (A, B, C...) within capacity."""
        if not self.is_open:
            raise SessionNotActiveError(
                f"Session {self.session_id} is closed and cannot seat diners."
            )
        if len(self.assigned_identifiers) >= self.guest_count:
            raise GuestCapacityExceededError(
                f"Table {self.table_number} already seated "
                f"{self.guest_count} diners."
            )
        next_identifier = DinerIdentifier.from_sequence(
            len(self.assigned_identifiers)
        )
        updated_session = replace(
            self,
            assigned_identifiers=(*self.assigned_identifiers, next_identifier),
        )
        return updated_session, next_identifier

    def close(self, closed_at: datetime) -> "TableSession":
        """Returns the closed version of the session, rejecting a second close."""
        if not self.is_open:
            raise SessionNotActiveError(
                f"Session {self.session_id} is already closed."
            )
        return replace(self, status=SessionStatus.CLOSED, closed_at=closed_at)
