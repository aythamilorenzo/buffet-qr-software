"""Unit tests for RestaurantPolicy validation of configurable buffet limits."""

import pytest

from app.domain.exceptions import InvalidRestaurantPolicyError
from app.domain.restaurant_policy import RestaurantPolicy


def test_policy_leaves_every_optional_rule_disabled_by_default() -> None:
    policy = RestaurantPolicy(max_diners_per_table=14)
    assert policy.max_diners_per_table == 14
    assert policy.max_dishes_per_round is None
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
