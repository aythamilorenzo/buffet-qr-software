"""In-memory fake of KitchenNotifierPort for use case tests."""

from app.domain.order_round import OrderRound
from app.ports.kitchen_notifier import KitchenNotifierPort


class FakeKitchenNotifier(KitchenNotifierPort):
    """Records notified rounds so tests can assert kitchen events."""

    def __init__(self) -> None:
        self.submitted_rounds: list[OrderRound] = []
        self.completed_rounds: list[OrderRound] = []

    async def notify_round_submitted(self, round_: OrderRound) -> None:
        self.submitted_rounds.append(round_)

    async def notify_round_completed(self, round_: OrderRound) -> None:
        self.completed_rounds.append(round_)
