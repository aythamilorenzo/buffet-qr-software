"""Unit tests for RemoveCartItemUseCase shared cart deletion flow."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.application.remove_cart_item_use_case import RemoveCartItemUseCase
from app.domain.cart_item import CartItem
from app.domain.exceptions import SessionNotActiveError, TableSessionNotFoundError
from app.domain.table_session import TableSession
from app.domain.value_objects import DinerIdentifier
from tests.fakes import FakeOrderRepository, FakeSessionRepository

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 25, 13, 0, tzinfo=UTC)


def build_cart_item(session_id: UUID) -> CartItem:
    return CartItem(
        session_id=session_id,
        diner_identifier=DinerIdentifier("A"),
        dish_id=uuid4(),
        dish_name="California Roll",
        station="sushi",
        quantity=2,
        added_at=NOW,
    )


async def build_use_case(
    session_repository: FakeSessionRepository,
    order_repository: FakeOrderRepository,
    session: TableSession,
) -> RemoveCartItemUseCase:
    await session_repository.save(session)
    return RemoveCartItemUseCase(
        session_repository=session_repository,
        order_repository=order_repository,
    )


async def test_remove_cart_item_deletes_the_line() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    session = TableSession(table_number="12", guest_count=4, opened_at=NOW)
    use_case = await build_use_case(session_repository, order_repository, session)
    item = build_cart_item(session.session_id)
    await order_repository.save_cart_item(item)
    await use_case.execute(session.session_id, item.item_id)
    assert await order_repository.list_cart_items(session.session_id) == []


async def test_remove_cart_item_is_idempotent_when_line_is_missing() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    session = TableSession(table_number="12", guest_count=4, opened_at=NOW)
    use_case = await build_use_case(session_repository, order_repository, session)
    await use_case.execute(session.session_id, uuid4())


async def test_remove_cart_item_rejects_unknown_session() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    session = TableSession(table_number="12", guest_count=4, opened_at=NOW)
    use_case = await build_use_case(session_repository, order_repository, session)
    with pytest.raises(TableSessionNotFoundError):
        await use_case.execute(uuid4(), uuid4())


async def test_remove_cart_item_rejects_a_closed_session() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    session = TableSession(
        table_number="12",
        guest_count=4,
        opened_at=NOW,
    ).close(LATER)
    use_case = await build_use_case(session_repository, order_repository, session)
    with pytest.raises(SessionNotActiveError):
        await use_case.execute(session.session_id, uuid4())
