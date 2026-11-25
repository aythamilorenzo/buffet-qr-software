"""Unit tests for OpenTableSessionUseCase policy and duplicate-table guards."""

from datetime import UTC, datetime

import pytest

from app.application.open_table_session_use_case import OpenTableSessionUseCase
from app.domain.exceptions import (
    MaxDinersPerTableExceededError,
    TableSessionAlreadyActiveError,
)
from app.domain.restaurant_policy import RestaurantPolicy
from tests.fakes import FakeSessionRepository

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
POLICY = RestaurantPolicy(max_diners_per_table=14)


def build_use_case(repository: FakeSessionRepository) -> OpenTableSessionUseCase:
    return OpenTableSessionUseCase(
        session_repository=repository,
        policy=POLICY,
    )


async def test_open_table_session_persists_a_new_open_session() -> None:
    repository = FakeSessionRepository()
    session = await build_use_case(repository).execute(
        table_number="12",
        guest_count=4,
        opened_at=NOW,
    )
    assert session.is_open
    assert session.table_number == "12"
    assert await repository.get_by_id(session.session_id) == session


async def test_open_table_session_rejects_guest_count_above_policy() -> None:
    repository = FakeSessionRepository()
    with pytest.raises(MaxDinersPerTableExceededError):
        await build_use_case(repository).execute(
            table_number="12",
            guest_count=15,
            opened_at=NOW,
        )
    assert await repository.list_active() == []


async def test_open_table_session_rejects_a_duplicate_active_table() -> None:
    repository = FakeSessionRepository()
    use_case = build_use_case(repository)
    await use_case.execute(table_number="12", guest_count=4, opened_at=NOW)
    with pytest.raises(TableSessionAlreadyActiveError):
        await use_case.execute(table_number="12", guest_count=2, opened_at=NOW)
    assert len(await repository.list_active()) == 1
