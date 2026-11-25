"""OrderRound entity: a batch of cart items submitted to the kitchen."""

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from app.domain.cart_item import CartItem
from app.domain.exceptions import (
    EmptyOrderRoundError,
    InvalidDomainValueError,
    RoundAlreadyCompletedError,
)
from app.domain.value_objects import DinerIdentifier


class RoundStatus(StrEnum):
    """Lifecycle states of a round inside the kitchen pipeline."""

    PENDING = "pending"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderRound:
    """Kitchen ticket grouping the cart items of one submission, immutable by design.

    A round snapshots its items at submission time so the kitchen ticket stays
    stable even after the shared cart is cleared. `round_number` is sequential
    per table session and lets the kitchen display rounds in arrival order.
    """

    round_id: UUID = field(default_factory=uuid4)
    session_id: UUID
    round_number: int
    items: tuple[CartItem, ...]
    submitted_by: DinerIdentifier
    submitted_at: datetime
    status: RoundStatus = RoundStatus.PENDING
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.round_number < 1:
            raise InvalidDomainValueError(
                f"round_number must be a positive integer, got {self.round_number}."
            )
        if not self.items:
            raise EmptyOrderRoundError(
                "An order round requires at least one cart item."
            )
        if any(item.session_id != self.session_id for item in self.items):
            raise InvalidDomainValueError(
                "Every cart item of an order round must belong to the round session."
            )
        if self.status is RoundStatus.COMPLETED and self.completed_at is None:
            raise InvalidDomainValueError(
                "A completed round requires a completed_at timestamp."
            )
        if self.status is RoundStatus.PENDING and self.completed_at is not None:
            raise InvalidDomainValueError(
                "A pending round must not carry a completed_at timestamp."
            )

    @property
    def total_dish_quantity(self) -> int:
        """Total dishes across every line, used for round-level policy checks."""
        return sum(item.quantity for item in self.items)

    def dish_quantity_per_diner(self) -> dict[DinerIdentifier, int]:
        """Dishes each diner contributed to this round, for per-guest policy checks."""
        quantities: dict[DinerIdentifier, int] = {}
        for item in self.items:
            quantities[item.diner_identifier] = (
                quantities.get(item.diner_identifier, 0) + item.quantity
            )
        return quantities

    def distinct_dish_count_per_diner(self) -> dict[DinerIdentifier, int]:
        """Distinct dishes each diner contributed, regardless of quantity."""
        dishes_per_diner: dict[DinerIdentifier, set[UUID]] = {}
        for item in self.items:
            dishes_per_diner.setdefault(item.diner_identifier, set()).add(
                item.dish_id,
            )
        return {
            identifier: len(dish_ids)
            for identifier, dish_ids in dishes_per_diner.items()
        }

    @property
    def total_distinct_dish_count(self) -> int:
        """Distinct dishes across every diner in this round."""
        return len({item.dish_id for item in self.items})

    def mark_completed(self, completed_at: datetime) -> "OrderRound":
        """Returns the completed version of the round, rejecting double completion."""
        if self.status is not RoundStatus.PENDING:
            raise RoundAlreadyCompletedError(
                f"Round {self.round_number} is already {self.status.value}."
            )
        return replace(
            self,
            status=RoundStatus.COMPLETED,
            completed_at=completed_at,
        )
