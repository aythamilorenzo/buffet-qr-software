"""Unit tests for MarkRoundCompletedUseCase kitchen completion flow."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.mark_round_completed_use_case import MarkRoundCompletedUseCase
from app.domain.cart_item import CartItem
from app.domain.exceptions import ConcurrentModificationError
from app.domain.order_round import OrderRound, RoundStatus
from app.domain.value_objects import DinerIdentifier
from tests.fakes import FakeKitchenNotifier, FakeOrderRepository

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 25, 12, 10, tzinfo=UTC)


def build_pending_round() -> OrderRound:
    session_id = uuid4()
    item = CartItem(
        session_id=session_id,
        diner_identifier=DinerIdentifier("A"),
        dish_id=uuid4(),
        dish_name="California Roll",
        station="sushi",
        quantity=2,
        added_at=NOW,
    )
    return OrderRound(
        session_id=session_id,
        round_number=1,
        items=(item,),
        submitted_by=DinerIdentifier("A"),
        submitted_at=NOW,
    )


def build_use_case(
    order_repository: FakeOrderRepository,
    kitchen_notifier: FakeKitchenNotifier,
) -> MarkRoundCompletedUseCase:
    return MarkRoundCompletedUseCase(
        order_repository=order_repository,
        kitchen_notifier=kitchen_notifier,
    )


async def test_mark_round_completed_persists_and_notifies_the_kds() -> None:
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    round_ = build_pending_round()
    await order_repository.submit_round(round_)
    use_case = build_use_case(order_repository, kitchen_notifier)
    completed_round = await use_case.execute(round_.round_id, LATER)
    assert completed_round.status is RoundStatus.COMPLETED
    assert completed_round.completed_at == LATER
    assert kitchen_notifier.completed_rounds == [completed_round]
    assert kitchen_notifier.submitted_rounds == []


async def test_mark_round_completed_rejects_unknown_round() -> None:
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    use_case = build_use_case(order_repository, kitchen_notifier)
    with pytest.raises(ConcurrentModificationError):
        await use_case.execute(uuid4(), LATER)
    assert kitchen_notifier.completed_rounds == []


async def test_mark_round_completed_rejects_a_double_completion() -> None:
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    round_ = build_pending_round()
    await order_repository.submit_round(round_)
    use_case = build_use_case(order_repository, kitchen_notifier)
    await use_case.execute(round_.round_id, LATER)
    with pytest.raises(ConcurrentModificationError):
        await use_case.execute(round_.round_id, LATER)
    assert len(kitchen_notifier.completed_rounds) == 1
