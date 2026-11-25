"""Unit tests for AddCartItemUseCase shared cart insertion guards."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.application.add_cart_item_use_case import AddCartItemUseCase
from app.domain.cart_item import CartItem
from app.domain.exceptions import (
    DinerNotAssignedToSessionError,
    SessionNotActiveError,
    TableSessionNotFoundError,
)
from app.domain.table_session import TableSession
from app.domain.value_objects import DinerIdentifier
from tests.fakes import FakeOrderRepository, FakeSessionRepository

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 25, 13, 0, tzinfo=UTC)


def build_use_case(
    session_repository: FakeSessionRepository,
    order_repository: FakeOrderRepository,
) -> AddCartItemUseCase:
    return AddCartItemUseCase(
        session_repository=session_repository,
        order_repository=order_repository,
    )


async def add_single_item(
    use_case: AddCartItemUseCase,
    session_id: UUID,
    identifier: DinerIdentifier,
) -> CartItem:
    return await use_case.execute(
        session_id=session_id,
        diner_identifier=identifier,
        dish_id=uuid4(),
        dish_name="California Roll",
        station="sushi",
        quantity=2,
        added_at=NOW,
    )


async def test_add_cart_item_persists_a_line_for_a_seated_diner() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    session = TableSession(table_number="12", guest_count=4, opened_at=NOW)
    seated_session, identifier = session.assign_next_identifier()
    await session_repository.save(seated_session)
    use_case = build_use_case(session_repository, order_repository)
    item = await add_single_item(use_case, seated_session.session_id, identifier)
    stored_items = await order_repository.list_cart_items(seated_session.session_id)
    assert stored_items == [item]
    assert item.diner_identifier == DinerIdentifier("A")


async def test_add_cart_item_rejects_unknown_session() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    use_case = build_use_case(session_repository, order_repository)
    with pytest.raises(TableSessionNotFoundError):
        await add_single_item(use_case, uuid4(), DinerIdentifier("A"))
    assert await order_repository.list_cart_items(uuid4()) == []


async def test_add_cart_item_rejects_a_closed_session() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    session = TableSession(table_number="12", guest_count=4, opened_at=NOW)
    seated_session, identifier = session.assign_next_identifier()
    closed_session = seated_session.close(LATER)
    await session_repository.save(closed_session)
    use_case = build_use_case(session_repository, order_repository)
    with pytest.raises(SessionNotActiveError):
        await add_single_item(use_case, closed_session.session_id, identifier)
    assert await order_repository.list_cart_items(closed_session.session_id) == []


async def test_add_cart_item_rejects_an_unassigned_diner_letter() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    session = TableSession(table_number="12", guest_count=4, opened_at=NOW)
    await session_repository.save(session)
    use_case = build_use_case(session_repository, order_repository)
    with pytest.raises(DinerNotAssignedToSessionError):
        await add_single_item(use_case, session.session_id, DinerIdentifier("A"))
    assert await order_repository.list_cart_items(session.session_id) == []
