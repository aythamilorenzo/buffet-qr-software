"""Unit tests for SubmitOrderRoundUseCase table batch submission flow."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.application.submit_order_round_use_case import SubmitOrderRoundUseCase
from app.domain.cart_item import CartItem
from app.domain.exceptions import (
    ConcurrentModificationError,
    DinerNotAssignedToSessionError,
    DishLimitExceededError,
    EmptyOrderRoundError,
    MaxPendingRoundsExceededError,
    RoundCooldownNotElapsedError,
    SessionNotActiveError,
    TableSessionNotFoundError,
)
from app.domain.restaurant_policy import RestaurantPolicy
from app.domain.table_session import TableSession
from app.domain.value_objects import DinerIdentifier
from tests.fakes import (
    FakeKitchenNotifier,
    FakeOrderRepository,
    FakeSessionRepository,
)

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
AFTER_COOLDOWN = NOW + timedelta(seconds=120)
DURING_COOLDOWN = NOW + timedelta(seconds=30)


def build_cart_item(
    session_id: UUID,
    diner_identifier: DinerIdentifier,
    quantity: int,
) -> CartItem:
    return CartItem(
        session_id=session_id,
        diner_identifier=diner_identifier,
        dish_id=uuid4(),
        dish_name="California Roll",
        station="sushi",
        quantity=quantity,
        added_at=NOW,
    )


def build_use_case(
    session_repository: FakeSessionRepository,
    order_repository: FakeOrderRepository,
    kitchen_notifier: FakeKitchenNotifier,
    policy: RestaurantPolicy,
) -> SubmitOrderRoundUseCase:
    return SubmitOrderRoundUseCase(
        session_repository=session_repository,
        order_repository=order_repository,
        kitchen_notifier=kitchen_notifier,
        policy=policy,
    )


async def save_seated_session(
    session_repository: FakeSessionRepository,
    diner_count: int = 2,
) -> tuple[TableSession, tuple[DinerIdentifier, ...]]:
    session = TableSession(table_number="12", guest_count=4, opened_at=NOW)
    identifiers: list[DinerIdentifier] = []
    for _ in range(diner_count):
        session, identifier = session.assign_next_identifier()
        identifiers.append(identifier)
    await session_repository.save(session)
    return session, tuple(identifiers)


class ConflictingRoundNumberRepository(FakeOrderRepository):
    """Always claims round number one to simulate a concurrent submission."""

    async def next_round_number(self, session_id: UUID) -> int:
        return 1


async def test_submit_round_packages_the_whole_table_cart() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    policy = RestaurantPolicy(max_diners_per_table=14)
    use_case = build_use_case(
        session_repository,
        order_repository,
        kitchen_notifier,
        policy,
    )
    session, (diner_a, diner_b) = await save_seated_session(session_repository)
    item_a = build_cart_item(session.session_id, diner_a, quantity=2)
    item_b = build_cart_item(session.session_id, diner_b, quantity=3)
    await order_repository.save_cart_item(item_a)
    await order_repository.save_cart_item(item_b)

    round_ = await use_case.execute(session.session_id, diner_a, NOW)

    assert round_.round_number == 1
    assert round_.submitted_by == diner_a
    assert round_.items == (item_a, item_b)
    assert round_.total_dish_quantity == 5
    assert await order_repository.list_cart_items(session.session_id) == []
    assert kitchen_notifier.submitted_rounds == [round_]


async def test_submit_round_numbers_rounds_sequentially() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    policy = RestaurantPolicy(max_diners_per_table=14)
    use_case = build_use_case(
        session_repository,
        order_repository,
        kitchen_notifier,
        policy,
    )
    session, (diner_a, diner_b) = await save_seated_session(session_repository)
    await order_repository.save_cart_item(
        build_cart_item(session.session_id, diner_a, quantity=1),
    )
    await use_case.execute(session.session_id, diner_a, NOW)
    await order_repository.save_cart_item(
        build_cart_item(session.session_id, diner_b, quantity=1),
    )

    second_round = await use_case.execute(session.session_id, diner_b, NOW)

    assert second_round.round_number == 2
    assert await order_repository.list_cart_items(session.session_id) == []


async def test_submit_round_rejects_an_empty_table_cart() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    policy = RestaurantPolicy(max_diners_per_table=14)
    use_case = build_use_case(
        session_repository,
        order_repository,
        kitchen_notifier,
        policy,
    )
    session, (diner_a,) = await save_seated_session(session_repository, 1)

    with pytest.raises(EmptyOrderRoundError):
        await use_case.execute(session.session_id, diner_a, NOW)

    assert kitchen_notifier.submitted_rounds == []


async def test_submit_round_enforces_per_guest_dish_limit() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    policy = RestaurantPolicy(
        max_diners_per_table=14,
        max_dishes_per_round=4,
    )
    use_case = build_use_case(
        session_repository,
        order_repository,
        kitchen_notifier,
        policy,
    )
    session, (diner_a,) = await save_seated_session(session_repository, 1)
    await order_repository.save_cart_item(
        build_cart_item(session.session_id, diner_a, quantity=5),
    )

    with pytest.raises(DishLimitExceededError):
        await use_case.execute(session.session_id, diner_a, NOW)

    assert len(await order_repository.list_cart_items(session.session_id)) == 1
    assert kitchen_notifier.submitted_rounds == []


async def test_submit_round_enforces_the_table_cooldown() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    policy = RestaurantPolicy(
        max_diners_per_table=14,
        round_cooldown_seconds=120,
    )
    use_case = build_use_case(
        session_repository,
        order_repository,
        kitchen_notifier,
        policy,
    )
    session, (diner_a,) = await save_seated_session(session_repository, 1)
    await order_repository.save_cart_item(
        build_cart_item(session.session_id, diner_a, quantity=1),
    )
    await use_case.execute(session.session_id, diner_a, NOW)
    await order_repository.save_cart_item(
        build_cart_item(session.session_id, diner_a, quantity=1),
    )

    with pytest.raises(RoundCooldownNotElapsedError):
        await use_case.execute(session.session_id, diner_a, DURING_COOLDOWN)

    await use_case.execute(session.session_id, diner_a, AFTER_COOLDOWN)
    assert len(kitchen_notifier.submitted_rounds) == 2


async def test_submit_round_enforces_the_pending_round_cap() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    policy = RestaurantPolicy(
        max_diners_per_table=14,
        max_pending_rounds=1,
    )
    use_case = build_use_case(
        session_repository,
        order_repository,
        kitchen_notifier,
        policy,
    )
    session, (diner_a,) = await save_seated_session(session_repository, 1)
    await order_repository.save_cart_item(
        build_cart_item(session.session_id, diner_a, quantity=1),
    )
    first_round = await use_case.execute(session.session_id, diner_a, NOW)
    await order_repository.save_cart_item(
        build_cart_item(session.session_id, diner_a, quantity=1),
    )

    with pytest.raises(MaxPendingRoundsExceededError):
        await use_case.execute(session.session_id, diner_a, NOW)

    await order_repository.mark_round_completed(first_round.round_id, NOW)
    third_round = await use_case.execute(session.session_id, diner_a, NOW)

    assert third_round.round_number == 2


async def test_submit_round_rejects_unknown_session() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    policy = RestaurantPolicy(max_diners_per_table=14)
    use_case = build_use_case(
        session_repository,
        order_repository,
        kitchen_notifier,
        policy,
    )
    with pytest.raises(TableSessionNotFoundError):
        await use_case.execute(uuid4(), DinerIdentifier("A"), NOW)


async def test_submit_round_rejects_a_closed_session() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    policy = RestaurantPolicy(max_diners_per_table=14)
    use_case = build_use_case(
        session_repository,
        order_repository,
        kitchen_notifier,
        policy,
    )
    session, (diner_a,) = await save_seated_session(session_repository, 1)
    closed_session = session.close(NOW + timedelta(hours=1))
    await session_repository.save(closed_session)

    with pytest.raises(SessionNotActiveError):
        await use_case.execute(closed_session.session_id, diner_a, NOW)


async def test_submit_round_rejects_an_unassigned_submitter() -> None:
    session_repository = FakeSessionRepository()
    order_repository = FakeOrderRepository()
    kitchen_notifier = FakeKitchenNotifier()
    policy = RestaurantPolicy(max_diners_per_table=14)
    use_case = build_use_case(
        session_repository,
        order_repository,
        kitchen_notifier,
        policy,
    )
    session, _ = await save_seated_session(session_repository, 1)
    await order_repository.save_cart_item(
        build_cart_item(session.session_id, DinerIdentifier("A"), quantity=1),
    )

    with pytest.raises(DinerNotAssignedToSessionError):
        await use_case.execute(session.session_id, DinerIdentifier("B"), NOW)


async def test_submit_round_propagates_a_concurrent_number_conflict() -> None:
    session_repository = FakeSessionRepository()
    order_repository = ConflictingRoundNumberRepository()
    kitchen_notifier = FakeKitchenNotifier()
    policy = RestaurantPolicy(max_diners_per_table=14)
    use_case = build_use_case(
        session_repository,
        order_repository,
        kitchen_notifier,
        policy,
    )
    session, (diner_a,) = await save_seated_session(session_repository, 1)
    await order_repository.save_cart_item(
        build_cart_item(session.session_id, diner_a, quantity=1),
    )
    await use_case.execute(session.session_id, diner_a, NOW)
    await order_repository.save_cart_item(
        build_cart_item(session.session_id, diner_a, quantity=1),
    )

    with pytest.raises(ConcurrentModificationError):
        await use_case.execute(session.session_id, diner_a, NOW)

    assert len(kitchen_notifier.submitted_rounds) == 1
    assert len(await order_repository.list_cart_items(session.session_id)) == 1
