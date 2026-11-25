"""Unit tests for RestaurantPolicy validation of configurable buffet limits."""

import pytest

from app.domain.exceptions import InvalidRestaurantPolicyError
from app.domain.restaurant_policy import RestaurantPolicy


def test_policy_defaults_leave_every_rule_disabled() -> None:
    policy = RestaurantPolicy()
    assert policy.max_dishes_per_round is None
    assert policy.round_cooldown_seconds is None
    assert policy.max_pending_rounds is None


def test_policy_accepts_positive_limits() -> None:
    policy = RestaurantPolicy(
        max_dishes_per_round=6,
        round_cooldown_seconds=120,
        max_pending_rounds=3,
    )
    assert policy.max_dishes_per_round == 6
    assert policy.round_cooldown_seconds == 120
    assert policy.max_pending_rounds == 3


@pytest.mark.parametrize(
    "field_name",
    ["max_dishes_per_round", "round_cooldown_seconds", "max_pending_rounds"],
)
@pytest.mark.parametrize("value", [0, -1])
def test_policy_rejects_non_positive_limits(field_name: str, value: int) -> None:
    with pytest.raises(InvalidRestaurantPolicyError):
        RestaurantPolicy(**{field_name: value})
