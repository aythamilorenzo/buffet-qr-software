"""Unit tests for the TableSession aggregate and its lifecycle transitions."""

from datetime import UTC, datetime

import pytest

from app.domain.exceptions import (
    GuestCapacityExceededError,
    InvalidDomainValueError,
    SessionNotActiveError,
)
from app.domain.table_session import SessionStatus, TableSession
from app.domain.value_objects import DinerIdentifier

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 25, 12, 30, tzinfo=UTC)


def build_open_session(guest_count: int = 4) -> TableSession:
    return TableSession(table_number="12", guest_count=guest_count, opened_at=NOW)


def test_open_session_starts_without_assigned_identifiers() -> None:
    session = build_open_session()
    assert session.status is SessionStatus.OPEN
    assert session.assigned_identifiers == ()
    assert session.closed_at is None
    assert session.is_open


def test_each_construction_generates_a_fresh_session_id() -> None:
    assert build_open_session().session_id != build_open_session().session_id


def test_empty_table_number_is_rejected() -> None:
    with pytest.raises(InvalidDomainValueError):
        TableSession(table_number="   ", guest_count=2, opened_at=NOW)


@pytest.mark.parametrize("guest_count", [0, -3, 27])
def test_guest_count_outside_the_alphabet_range_is_rejected(
    guest_count: int,
) -> None:
    with pytest.raises(InvalidDomainValueError):
        TableSession(table_number="12", guest_count=guest_count, opened_at=NOW)


def test_assign_next_identifier_seeds_diners_sequentially() -> None:
    session = build_open_session(guest_count=3)
    session, first = session.assign_next_identifier()
    session, second = session.assign_next_identifier()
    assert first == DinerIdentifier("A")
    assert second == DinerIdentifier("B")
    assert session.assigned_identifiers == (
        DinerIdentifier("A"),
        DinerIdentifier("B"),
    )


def test_assign_next_identifier_stops_at_guest_capacity() -> None:
    session = build_open_session(guest_count=1)
    session, _ = session.assign_next_identifier()
    with pytest.raises(GuestCapacityExceededError):
        session.assign_next_identifier()


def test_closed_session_rejects_diner_assignment() -> None:
    closed_session = build_open_session().close(LATER)
    with pytest.raises(SessionNotActiveError):
        closed_session.assign_next_identifier()


def test_close_transitions_session_and_rejects_a_second_close() -> None:
    closed_session = build_open_session().close(LATER)
    assert closed_session.status is SessionStatus.CLOSED
    assert closed_session.closed_at == LATER
    assert not closed_session.is_open
    with pytest.raises(SessionNotActiveError):
        closed_session.close(LATER)


def test_closed_session_requires_a_close_timestamp() -> None:
    with pytest.raises(InvalidDomainValueError):
        TableSession(
            table_number="12",
            guest_count=2,
            opened_at=NOW,
            status=SessionStatus.CLOSED,
        )


def test_open_session_must_not_carry_a_close_timestamp() -> None:
    with pytest.raises(InvalidDomainValueError):
        TableSession(
            table_number="12",
            guest_count=2,
            opened_at=NOW,
            closed_at=LATER,
        )
