"""Unit tests for AssignDinerIdentifierUseCase sequential diner letters."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.assign_diner_identifier_use_case import (
    AssignDinerIdentifierUseCase,
)
from app.domain.exceptions import (
    GuestCapacityExceededError,
    SessionNotActiveError,
    TableSessionNotFoundError,
)
from app.domain.table_session import TableSession
from app.domain.value_objects import DinerIdentifier
from tests.fakes import FakeSessionRepository

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 25, 13, 0, tzinfo=UTC)


async def test_assign_diner_identifier_seats_letters_sequentially() -> None:
    repository = FakeSessionRepository()
    session = TableSession(table_number="12", guest_count=2, opened_at=NOW)
    await repository.save(session)
    use_case = AssignDinerIdentifierUseCase(session_repository=repository)
    _, first = await use_case.execute(session.session_id)
    second_session, second = await use_case.execute(session.session_id)
    assert first == DinerIdentifier("A")
    assert second == DinerIdentifier("B")
    assert second_session.assigned_identifiers == (
        DinerIdentifier("A"),
        DinerIdentifier("B"),
    )


async def test_assign_diner_identifier_rejects_unknown_session() -> None:
    repository = FakeSessionRepository()
    use_case = AssignDinerIdentifierUseCase(session_repository=repository)
    with pytest.raises(TableSessionNotFoundError):
        await use_case.execute(uuid4())


async def test_assign_diner_identifier_stops_at_guest_capacity() -> None:
    repository = FakeSessionRepository()
    session = TableSession(table_number="12", guest_count=1, opened_at=NOW)
    await repository.save(session)
    use_case = AssignDinerIdentifierUseCase(session_repository=repository)
    await use_case.execute(session.session_id)
    with pytest.raises(GuestCapacityExceededError):
        await use_case.execute(session.session_id)


async def test_assign_diner_identifier_rejects_a_closed_session() -> None:
    repository = FakeSessionRepository()
    closed_session = TableSession(
        table_number="12",
        guest_count=2,
        opened_at=NOW,
    ).close(LATER)
    await repository.save(closed_session)
    use_case = AssignDinerIdentifierUseCase(session_repository=repository)
    with pytest.raises(SessionNotActiveError):
        await use_case.execute(closed_session.session_id)
