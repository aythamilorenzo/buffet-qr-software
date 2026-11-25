"""RestaurantPolicy: the configurable operational limits that govern order rounds."""

from dataclasses import dataclass

from app.domain.exceptions import InvalidRestaurantPolicyError


@dataclass(frozen=True, slots=True)
class RestaurantPolicy:
    """Configurable buffet rules applied to every table session of a restaurant.

    Every limit is optional: `None` means the rule is disabled, and it is the
    single representation of "disabled" (zero is not accepted). No buffet rule
    is ever hardcoded elsewhere; use cases must evaluate their validations
    against an instance of this entity.
    """

    max_dishes_per_round: int | None = None
    round_cooldown_seconds: int | None = None
    max_pending_rounds: int | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("max_dishes_per_round", self.max_dishes_per_round),
            ("round_cooldown_seconds", self.round_cooldown_seconds),
            ("max_pending_rounds", self.max_pending_rounds),
        ):
            if value is not None and value < 1:
                raise InvalidRestaurantPolicyError(
                    f"{field_name} must be None or a positive integer, got {value}."
                )
