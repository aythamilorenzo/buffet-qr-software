"""Port for the shared table cart and the kitchen round pipeline."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.cart_item import CartItem
from app.domain.order_round import OrderRound


class OrderRepositoryPort(ABC):
    """Contract the application layer uses to move carts into kitchen rounds.

    Every mutating method must execute as a single atomic operation. Round
    submission is serialized per session (row-level lock or equivalent), so a
    stale `round_number` computed by a concurrent writer raises
    `ConcurrentModificationError` instead of overwriting another round.
    """

    @abstractmethod
    async def list_cart_items(self, session_id: UUID) -> list[CartItem]:
        """Returns the shared cart lines of a session in insertion order."""

    @abstractmethod
    async def save_cart_item(self, item: CartItem) -> None:
        """Adds one line to the shared cart as an atomic insert."""

    @abstractmethod
    async def remove_cart_item(self, session_id: UUID, item_id: UUID) -> None:
        """Deletes one cart line of the session as an atomic delete."""

    @abstractmethod
    async def next_round_number(self, session_id: UUID) -> int:
        """Returns the sequential number the next round of a session must use."""

    @abstractmethod
    async def submit_round(self, round_: OrderRound) -> OrderRound:
        """Atomically inserts a round and removes the cart lines it snapshots.

        Raises ConcurrentModificationError when a concurrent submission already
        claimed the round_number, so the caller can recompute and retry.
        """

    @abstractmethod
    async def get_last_round(self, session_id: UUID) -> OrderRound | None:
        """Returns the most recently submitted round of a session, or None."""

    @abstractmethod
    async def count_pending_rounds(self, session_id: UUID) -> int:
        """Returns how many rounds of the session still await kitchen completion."""

    @abstractmethod
    async def list_pending_rounds(self) -> list[OrderRound]:
        """Returns every kitchen round still pending, for the KDS view."""

    @abstractmethod
    async def mark_round_completed(
        self,
        round_id: UUID,
        completed_at: datetime,
    ) -> None:
        """Flags a pending round as completed in one atomic update.

        Raises ConcurrentModificationError when the round is missing or is no
        longer pending, so KDS clients converge on a single completion.
        """
