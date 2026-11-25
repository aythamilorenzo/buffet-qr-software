"""Unit tests for RestaurantPolicy validation and configurable round rules."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.domain.cart_item import CartItem
from app.domain.exceptions import (
    DishLimitExceededError,
    InvalidRestaurantPolicyError,
    MaxPendingRoundsExceededError,
    RoundCooldownNotElapsedError,
)
from app.domain.order_round import OrderRound
from app.domain.restaurant_policy import (
    DishCountingMode,
    DishLimitScope,
    RestaurantPolicy,
)
from app.domain.value_objects import DinerIdentifier

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
SESSION_ID = uuid4()


def build_cart_item(
    diner_letter: str,
    dish_name: str,
    quantity: int,
    dish_id: UUID | None = None,
) -> CartItem:
    return CartItem(
        session_id=SESSION_ID,
        diner_identifier=DinerIdentifier(diner_letter),
        dish_id=dish_id if dish_id is not None else uuid4(),
        dish_name=dish_name,
        station="sushi",
        quantity=quantity,
        added_at=NOW,
    )


def build_round(items: tuple[CartItem, ...]) -> OrderRound:
    return OrderRound(
        session_id=SESSION_ID,
        round_number=1,
        items=items,
        submitted_by=DinerIdentifier("A"),
        submitted_at=NOW,
    )


def test_policy_leaves_every_optional_rule_disabled_by_default() -> None:
    policy = RestaurantPolicy(max_diners_per_table=14)
    assert policy.max_dishes_per_round is None
    assert policy.dish_counting_mode is DishCountingMode.QUANTITY
    assert policy.dish_limit_scope is DishLimitScope.PER_DINER
    assert policy.round_cooldown_seconds is None
    assert policy.max_pending_rounds is None


def test_policy_accepts_positive_limits() -> None:
    policy = RestaurantPolicy(
        max_diners_per_table=14,
        max_dishes_per_round=6,
        round_cooldown_seconds=120,
        max_pending_rounds=3,
    )
    assert policy.max_dishes_per_round == 6
    assert policy.round_cooldown_seconds == 120
    assert policy.max_pending_rounds == 3


@pytest.mark.parametrize("value", [0, -1, 27])
def test_policy_rejects_seat_caps_outside_the_diner_alphabet(value: int) -> None:
    with pytest.raises(InvalidRestaurantPolicyError):
        RestaurantPolicy(max_diners_per_table=value)


@pytest.mark.parametrize(
    "field_name",
    ["max_dishes_per_round", "round_cooldown_seconds", "max_pending_rounds"],
)
@pytest.mark.parametrize("value", [0, -1])
def test_policy_rejects_non_positive_limits(field_name: str, value: int) -> None:
    with pytest.raises(InvalidRestaurantPolicyError):
        RestaurantPolicy(max_diners_per_table=14, **{field_name: value})


def test_policy_rejects_unknown_limit_semantics() -> None:
    with pytest.raises(InvalidRestaurantPolicyError):
        RestaurantPolicy(max_diners_per_table=14, dish_counting_mode="units")
    with pytest.raises(InvalidRestaurantPolicyError):
        RestaurantPolicy(max_diners_per_table=14, dish_limit_scope="all")


def test_dish_limit_counts_quantities_per_diner_by_default() -> None:
    policy = RestaurantPolicy(max_diners_per_table=14, max_dishes_per_round=4)
    round_ = build_round(
        (
            build_cart_item("A", "California Roll", quantity=2),
            build_cart_item("A", "Gyoza", quantity=3),
        ),
    )
    with pytest.raises(DishLimitExceededError):
        policy.enforce_dish_limit(round_)


def test_dish_limit_allows_quantities_within_the_per_diner_cap() -> None:
    policy = RestaurantPolicy(max_diners_per_table=14, max_dishes_per_round=4)
    round_ = build_round(
        (
            build_cart_item("A", "California Roll", quantity=4),
            build_cart_item("B", "Gyoza", quantity=4),
        ),
    )
    policy.enforce_dish_limit(round_)


def test_dish_limit_counts_distinct_dishes_when_configured() -> None:
    policy = RestaurantPolicy(
        max_diners_per_table=14,
        max_dishes_per_round=4,
        dish_counting_mode=DishCountingMode.DISTINCT_DISHES,
    )
    sushi_id = uuid4()
    repeated_dish_round = build_round(
        (
            build_cart_item("A", "California Roll", quantity=10, dish_id=sushi_id),
            build_cart_item("A", "California Roll", quantity=5, dish_id=sushi_id),
        ),
    )
    policy.enforce_dish_limit(repeated_dish_round)

    overloaded_round = build_round(
        tuple(
            build_cart_item("A", f"Dish {index}", quantity=1)
            for index in range(5)
        ),
    )
    with pytest.raises(DishLimitExceededError):
        policy.enforce_dish_limit(overloaded_round)


def test_dish_limit_sums_all_diners_for_table_total_scope() -> None:
    policy = RestaurantPolicy(
        max_diners_per_table=14,
        max_dishes_per_round=4,
        dish_limit_scope=DishLimitScope.TABLE_TOTAL,
    )
    passing_round = build_round(
        (
            build_cart_item("A", "California Roll", quantity=2),
            build_cart_item("B", "Gyoza", quantity=2),
        ),
    )
    policy.enforce_dish_limit(passing_round)

    failing_round = build_round(
        (
            build_cart_item("A", "California Roll", quantity=3),
            build_cart_item("B", "Gyoza", quantity=2),
        ),
    )
    with pytest.raises(DishLimitExceededError):
        policy.enforce_dish_limit(failing_round)


def test_dish_limit_combines_distinct_dishes_with_table_total() -> None:
    policy = RestaurantPolicy(
        max_diners_per_table=14,
        max_dishes_per_round=2,
        dish_counting_mode=DishCountingMode.DISTINCT_DISHES,
        dish_limit_scope=DishLimitScope.TABLE_TOTAL,
    )
    shared_dish_round = build_round(
        (
            build_cart_item("A", "California Roll", quantity=8),
            build_cart_item("B", "California Roll", quantity=9),
        ),
    )
    policy.enforce_dish_limit(shared_dish_round)

    overloaded_round = build_round(
        (
            build_cart_item("A", "California Roll", quantity=1),
            build_cart_item("B", "Gyoza", quantity=1),
            build_cart_item("B", "Ramen", quantity=1),
        ),
    )
    with pytest.raises(DishLimitExceededError):
        policy.enforce_dish_limit(overloaded_round)


def test_round_cooldown_requires_the_configured_wait() -> None:
    policy = RestaurantPolicy(
        max_diners_per_table=14,
        round_cooldown_seconds=120,
    )
    last_round = build_round((build_cart_item("A", "California Roll", 1),))
    with pytest.raises(RoundCooldownNotElapsedError):
        policy.enforce_round_cooldown(last_round, NOW + timedelta(seconds=30))
    policy.enforce_round_cooldown(last_round, NOW + timedelta(seconds=120))


def test_round_cooldown_passes_without_rules_or_previous_rounds() -> None:
    without_rule = RestaurantPolicy(max_diners_per_table=14)
    last_round = build_round((build_cart_item("A", "California Roll", 1),))
    without_rule.enforce_round_cooldown(last_round, NOW)

    with_rule = RestaurantPolicy(
        max_diners_per_table=14,
        round_cooldown_seconds=120,
    )
    with_rule.enforce_round_cooldown(None, NOW)


def test_pending_round_limit_rejects_when_the_kitchen_is_full() -> None:
    policy = RestaurantPolicy(
        max_diners_per_table=14,
        max_pending_rounds=1,
    )
    policy.enforce_pending_round_limit(0)
    with pytest.raises(MaxPendingRoundsExceededError):
        policy.enforce_pending_round_limit(1)


def test_pending_round_limit_passes_without_a_rule() -> None:
    policy = RestaurantPolicy(max_diners_per_table=14)
    policy.enforce_pending_round_limit(999)
