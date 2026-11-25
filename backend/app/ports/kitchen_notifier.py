"""Port for pushing kitchen events to every active kitchen consumer."""

from abc import ABC, abstractmethod

from app.domain.order_round import OrderRound


class KitchenNotifierPort(ABC):
    """Contract for delivering rounds to the kitchen output medium.

    Adapters decide the transport: a WebSocket broadcast feeds the KDS view,
    while a thermal printer adapter emits the paper ticket. The application
    core only states which events must reach the kitchen.
    """

    @abstractmethod
    async def notify_round_submitted(self, round_: OrderRound) -> None:
        """Delivers a newly pending round to every kitchen consumer."""

    @abstractmethod
    async def notify_round_completed(self, round_: OrderRound) -> None:
        """Announces that a round left the kitchen pipeline as completed."""
