"""Use case that completes a pending kitchen round and announces it."""

from datetime import datetime
from uuid import UUID

from app.domain.order_round import OrderRound
from app.ports.kitchen_notifier import KitchenNotifierPort
from app.ports.order_repository import OrderRepositoryPort


class MarkRoundCompletedUseCase:
    """Transitions a round out of the kitchen pipeline and notifies the KDS.

    The repository performs the transition atomically and returns the stored
    round, so the completion event carries the exact state every kitchen
    consumer must converge on.
    """

    def __init__(
        self,
        order_repository: OrderRepositoryPort,
        kitchen_notifier: KitchenNotifierPort,
    ) -> None:
        self._order_repository = order_repository
        self._kitchen_notifier = kitchen_notifier

    async def execute(self, round_id: UUID, completed_at: datetime) -> OrderRound:
        completed_round = await self._order_repository.mark_round_completed(
            round_id,
            completed_at,
        )
        await self._kitchen_notifier.notify_round_completed(completed_round)
        return completed_round
