"""In-memory fake of OrderRepositoryPort for use case tests."""

from datetime import datetime
from uuid import UUID

from app.domain.cart_item import CartItem
from app.domain.exceptions import ConcurrentModificationError
from app.domain.order_round import OrderRound, RoundStatus
from app.ports.order_repository import OrderRepositoryPort


class FakeOrderRepository(OrderRepositoryPort):
    """Stores cart lines and rounds in dictionaries without PostgreSQL."""

    def __init__(self) -> None:
        self._cart_items: dict[UUID, CartItem] = {}
        self._rounds: dict[UUID, OrderRound] = {}

    async def list_cart_items(self, session_id: UUID) -> list[CartItem]:
        session_items = (
            item
            for item in self._cart_items.values()
            if item.session_id == session_id
        )
        return sorted(session_items, key=lambda item: item.added_at)

    async def save_cart_item(self, item: CartItem) -> None:
        self._cart_items[item.item_id] = item

    async def remove_cart_item(self, session_id: UUID, item_id: UUID) -> None:
        item = self._cart_items.get(item_id)
        if item is not None and item.session_id == session_id:
            del self._cart_items[item_id]

    async def next_round_number(self, session_id: UUID) -> int:
        return max(
            (
                round_.round_number
                for round_ in self._rounds.values()
                if round_.session_id == session_id
            ),
            default=0,
        ) + 1

    async def submit_round(self, round_: OrderRound) -> OrderRound:
        self._ensure_round_number_is_free(round_)
        self._rounds[round_.round_id] = round_
        for item in round_.items:
            self._cart_items.pop(item.item_id, None)
        return round_

    async def get_last_round(self, session_id: UUID) -> OrderRound | None:
        session_rounds = (
            round_
            for round_ in self._rounds.values()
            if round_.session_id == session_id
        )
        return max(session_rounds, key=lambda round_: round_.submitted_at, default=None)

    async def count_pending_rounds(self, session_id: UUID) -> int:
        return sum(
            1
            for round_ in self._rounds.values()
            if round_.session_id == session_id
            and round_.status is RoundStatus.PENDING
        )

    async def list_pending_rounds(self) -> list[OrderRound]:
        pending_rounds = (
            round_
            for round_ in self._rounds.values()
            if round_.status is RoundStatus.PENDING
        )
        return sorted(pending_rounds, key=lambda round_: round_.submitted_at)

    async def mark_round_completed(
        self,
        round_id: UUID,
        completed_at: datetime,
    ) -> OrderRound:
        round_ = self._rounds.get(round_id)
        if round_ is None or round_.status is not RoundStatus.PENDING:
            raise ConcurrentModificationError(
                f"Round {round_id} is missing or no longer pending."
            )
        completed_round = round_.mark_completed(completed_at)
        self._rounds[round_id] = completed_round
        return completed_round

    def _ensure_round_number_is_free(self, round_: OrderRound) -> None:
        conflicting_round = next(
            (
                existing
                for existing in self._rounds.values()
                if existing.session_id == round_.session_id
                and existing.round_number == round_.round_number
            ),
            None,
        )
        if conflicting_round is not None:
            raise ConcurrentModificationError(
                f"Round number {round_.round_number} already exists for session "
                f"{round_.session_id}."
            )
