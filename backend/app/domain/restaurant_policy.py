"""RestaurantPolicy: the configurable operational limits that govern order rounds."""

from dataclasses import dataclass

from app.domain.exceptions import InvalidRestaurantPolicyError
from app.domain.value_objects import MAX_DINER_IDENTIFIERS


@dataclass(frozen=True, slots=True, kw_only=True)
class RestaurantPolicy:
    """Configurable buffet rules applied to every table session of a restaurant.

    `max_diners_per_table` is the physical seat cap a waiter may declare when
    activating a table, so each restaurant configures its own value. The
    remaining limits are optional: `None` means the rule is disabled and is
    its single representation (zero is not accepted). No buffet rule is ever
    hardcoded elsewhere; use cases must evaluate their validations against an
    instance of this entity.
    """

    max_diners_per_table: int
    max_dishes_per_round: int | None = None
    round_cooldown_seconds: int | None = None
    max_pending_rounds: int | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.max_diners_per_table <= MAX_DINER_IDENTIFIERS:
            raise InvalidRestaurantPolicyError(
                "max_diners_per_table must be between 1 and "
                f"{MAX_DINER_IDENTIFIERS}, got {self.max_diners_per_table}."
            )
        for field_name, value in (
            ("max_dishes_per_round", self.max_dishes_per_round),
            ("round_cooldown_seconds", self.round_cooldown_seconds),
            ("max_pending_rounds", self.max_pending_rounds),
        ):
            if value is not None and value < 1:
                raise InvalidRestaurantPolicyError(
                    f"{field_name} must be None or a positive integer, got {value}."
                )
