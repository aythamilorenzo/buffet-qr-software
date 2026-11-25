"""Unit tests for CloseTableSessionUseCase session shutdown flow."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.close_table_session_use_case import CloseTableSessionUseCase
from app.domain.exceptions import SessionNotActiveError, TableSessionNotFoundError
from app.domain.table_session import SessionStatus, TableSession
from tests.fakes import FakeSessionRepository

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 25, 13, 0, tzinfo=UTC)


def build_open_session() -> TableSession:
    return TableSession(table_number="12", guest_count=4, opened_at=NOW)


async def test_close_table_session_persists_the_closed_state() -> None:
    repository = FakeSessionRepository()
    session = build_open_session()
    await repository.save(session)
    use_case = CloseTableSessionUseCase(session_repository=repository)
    closed_session = await use_case.execute(session.session_id, LATER)
    assert closed_session.status is SessionStatus.CLOSED
    stored_session = await repository.get_by_id(session.session_id)
    assert stored_session is not None
    assert stored_session.status is SessionStatus.CLOSED


async def test_close_table_session_rejects_unknown_session() -> None:
    repository = FakeSessionRepository()
    use_case = CloseTableSessionUseCase(session_repository=repository)
    with pytest.raises(TableSessionNotFoundError):
        await use_case.execute(uuid4(), LATER)


async def test_close_table_session_rejects_a_second_close() -> None:
    repository = FakeSessionRepository()
    session = build_open_session()
    await repository.save(session)
    use_case = CloseTableSessionUseCase(session_repository=repository)
    await use_case.execute(session.session_id, LATER)
    with pytest.raises(SessionNotActiveError):
        await use_case.execute(session.session_id, LATER)
