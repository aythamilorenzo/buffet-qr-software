"""RestaurantPolicy: the configurable operational limits that govern order rounds."""

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.exceptions import (
    DishLimitExceededError,
    InvalidRestaurantPolicyError,
    MaxPendingRoundsExceededError,
    RoundCooldownNotElapsedError,
)
from app.domain.order_round import OrderRound
from app.domain.value_objects import MAX_DINER_IDENTIFIERS, DinerIdentifier


class DishCountingMode(StrEnum):
    """What counts as one dish when the restaurant dish limit is evaluated."""

    QUANTITY = "quantity"
    DISTINCT_DISHES = "distinct_dishes"


class DishLimitScope(StrEnum):
    """Who the restaurant dish limit applies to."""

    PER_DINER = "per_diner"
    TABLE_TOTAL = "table_total"


@dataclass(frozen=True, slots=True, kw_only=True)
class RestaurantPolicy:
    """Configurable buffet rules applied to every table session of a restaurant.

    Every limit is optional: `None` means the rule is disabled and is its
    single representation (zero is not accepted). The dish limit is a rule
    whose *semantics* are also configuration: `dish_counting_mode` chooses
    whether units or distinct menu items count as one dish, and
    `dish_limit_scope` chooses whether each diner or the whole table shares
    the cap. The defaults preserve the baseline behaviour (units per diner),
    so each restaurant adapts the rule by configuration alone. No buffet rule
    is ever hardcoded elsewhere; use cases must evaluate their validations
    against an instance of this entity.
    """

    max_diners_per_table: int
    max_dishes_per_round: int | None = None
    dish_counting_mode: DishCountingMode = DishCountingMode.QUANTITY
    dish_limit_scope: DishLimitScope = DishLimitScope.PER_DINER
    round_cooldown_seconds: int | None = None
    max_pending_rounds: int | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.max_diners_per_table <= MAX_DINER_IDENTIFIERS:
            raise InvalidRestaurantPolicyError(
                "max_diners_per_table must be between 1 and "
                f"{MAX_DINER_IDENTIFIERS}, got {self.max_diners_per_table}."
            )
        if self.dish_counting_mode not in DishCountingMode:
            raise InvalidRestaurantPolicyError(
                "dish_counting_mode must be a DishCountingMode value, "
                f"got {self.dish_counting_mode!r}."
            )
        if self.dish_limit_scope not in DishLimitScope:
            raise InvalidRestaurantPolicyError(
                "dish_limit_scope must be a DishLimitScope value, "
                f"got {self.dish_limit_scope!r}."
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

    def enforce_dish_limit(self, round_: OrderRound) -> None:
        """Raises when the round breaks the configured dish limit rule.

        The rule is assembled from configuration: the counting mode decides
        what counts as one dish and the scope decides who shares the cap.
        """
        if self.max_dishes_per_round is None:
            return
        for label, count in self._counted_dishes(round_):
            if count > self.max_dishes_per_round:
                raise DishLimitExceededError(
                    f"{label} has {count} dishes in this round but the policy "
                    f"allows at most {self.max_dishes_per_round} dishes per "
                    f"round."
                )

    def enforce_round_cooldown(
        self,
        last_round: OrderRound | None,
        submitted_at: datetime,
    ) -> None:
        """Raises when a round is submitted before the per-table wait elapsed.

        The wait is counted per table session from the submission of the
        last round; `None` disables the rule.
        """
        if self.round_cooldown_seconds is None or last_round is None:
            return
        elapsed_seconds = (
            submitted_at - last_round.submitted_at
        ).total_seconds()
        if elapsed_seconds >= self.round_cooldown_seconds:
            return
        remaining_seconds = math.ceil(
            self.round_cooldown_seconds - elapsed_seconds,
        )
        raise RoundCooldownNotElapsedError(
            f"The table must wait {remaining_seconds} seconds before "
            f"submitting another round."
        )

    def enforce_pending_round_limit(self, pending_rounds: int) -> None:
        """Raises when the kitchen already holds the allowed pending rounds."""
        if self.max_pending_rounds is None:
            return
        if pending_rounds >= self.max_pending_rounds:
            raise MaxPendingRoundsExceededError(
                f"The kitchen already holds {pending_rounds} rounds for this "
                f"table but the policy allows at most "
                f"{self.max_pending_rounds}."
            )

    def _counted_dishes(self, round_: OrderRound) -> list[tuple[str, int]]:
        if self.dish_limit_scope is DishLimitScope.TABLE_TOTAL:
            return [("The table", self._table_dish_count(round_))]
        return [
            (f"Diner {identifier}", count)
            for identifier, count in self._diner_dish_counts(round_).items()
        ]

    def _diner_dish_counts(
        self,
        round_: OrderRound,
    ) -> dict[DinerIdentifier, int]:
        if self.dish_counting_mode is DishCountingMode.QUANTITY:
            return round_.dish_quantity_per_diner()
        return round_.distinct_dish_count_per_diner()

    def _table_dish_count(self, round_: OrderRound) -> int:
        if self.dish_counting_mode is DishCountingMode.QUANTITY:
            return round_.total_dish_quantity
        return round_.total_distinct_dish_count
