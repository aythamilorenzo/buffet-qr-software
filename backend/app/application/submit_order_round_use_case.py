"""Use case that submits the shared cart of a table as one kitchen round."""

from datetime import datetime
from uuid import UUID

from app.domain.exceptions import (
    DinerNotAssignedToSessionError,
    EmptyOrderRoundError,
    SessionNotActiveError,
    TableSessionNotFoundError,
)
from app.domain.order_round import OrderRound
from app.domain.restaurant_policy import RestaurantPolicy
from app.domain.value_objects import DinerIdentifier
from app.ports.kitchen_notifier import KitchenNotifierPort
from app.ports.order_repository import OrderRepositoryPort
from app.ports.session_repository import SessionRepositoryPort


class SubmitOrderRoundUseCase:
    """Packages every pending cart line of a table into one kitchen round.

    The round snapshots the whole shared cart of the session, so the kitchen
    receives a single table batch while each line keeps its diner attribution
    for cart display and policy checks. Every rule (dish limit semantics,
    optional cooldown and pending round cap) is evaluated by the
    RestaurantPolicy instance, and the atomic submission removes the
    snapshotted cart lines in the same step.
    """

    def __init__(
        self,
        session_repository: SessionRepositoryPort,
        order_repository: OrderRepositoryPort,
        kitchen_notifier: KitchenNotifierPort,
        policy: RestaurantPolicy,
    ) -> None:
        self._session_repository = session_repository
        self._order_repository = order_repository
        self._kitchen_notifier = kitchen_notifier
        self._policy = policy

    async def execute(
        self,
        session_id: UUID,
        submitted_by: DinerIdentifier,
        submitted_at: datetime,
    ) -> OrderRound:
        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise TableSessionNotFoundError(
                f"Table session {session_id} does not exist."
            )
        if not session.is_open:
            raise SessionNotActiveError(
                f"Session {session_id} is closed and no longer accepts rounds."
            )
        if submitted_by not in session.assigned_identifiers:
            raise DinerNotAssignedToSessionError(
                f"Diner {submitted_by} was never seated at session "
                f"{session_id}."
            )
        pending_items = await self._order_repository.list_cart_items(session_id)
        if not pending_items:
            raise EmptyOrderRoundError(
                f"Session {session_id} has no pending cart items to submit."
            )
        round_ = OrderRound(
            session_id=session_id,
            round_number=await self._order_repository.next_round_number(
                session_id,
            ),
            items=tuple(pending_items),
            submitted_by=submitted_by,
            submitted_at=submitted_at,
        )
        last_round = await self._order_repository.get_last_round(session_id)
        pending_rounds = await self._order_repository.count_pending_rounds(
            session_id,
        )
        self._policy.enforce_dish_limit(round_)
        self._policy.enforce_round_cooldown(last_round, submitted_at)
        self._policy.enforce_pending_round_limit(pending_rounds)
        stored_round = await self._order_repository.submit_round(round_)
        await self._kitchen_notifier.notify_round_submitted(stored_round)
        return stored_round
