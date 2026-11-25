"""Use case that submits the shared cart of a table as one kitchen round."""

import math
from datetime import datetime
from uuid import UUID

from app.domain.exceptions import (
    DinerNotAssignedToSessionError,
    DishLimitExceededError,
    EmptyOrderRoundError,
    MaxPendingRoundsExceededError,
    RoundCooldownNotElapsedError,
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
    for cart display and per-guest policy checks. Per-guest dish limit,
    optional cooldown and pending round cap are evaluated against the
    RestaurantPolicy instance before anything reaches the kitchen, and the
    atomic submission removes the snapshotted cart lines in the same step.
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
        await self._enforce_policy(session_id, round_, submitted_at)
        stored_round = await self._order_repository.submit_round(round_)
        await self._kitchen_notifier.notify_round_submitted(stored_round)
        return stored_round

    async def _enforce_policy(
        self,
        session_id: UUID,
        round_: OrderRound,
        submitted_at: datetime,
    ) -> None:
        self._enforce_dish_limit(round_)
        await self._enforce_cooldown(session_id, submitted_at)
        await self._enforce_pending_round_limit(session_id)

    def _enforce_dish_limit(self, round_: OrderRound) -> None:
        if self._policy.max_dishes_per_round is None:
            return
        for diner_identifier, quantity in round_.dish_quantity_per_diner().items():
            if quantity > self._policy.max_dishes_per_round:
                raise DishLimitExceededError(
                    f"Diner {diner_identifier} ordered {quantity} dishes in "
                    f"this round but the policy allows at most "
                    f"{self._policy.max_dishes_per_round} per diner."
                )

    async def _enforce_cooldown(
        self,
        session_id: UUID,
        submitted_at: datetime,
    ) -> None:
        if self._policy.round_cooldown_seconds is None:
            return
        last_round = await self._order_repository.get_last_round(session_id)
        if last_round is None:
            return
        elapsed_seconds = (submitted_at - last_round.submitted_at).total_seconds()
        if elapsed_seconds < self._policy.round_cooldown_seconds:
            remaining_seconds = math.ceil(
                self._policy.round_cooldown_seconds - elapsed_seconds,
            )
            raise RoundCooldownNotElapsedError(
                f"Session {session_id} must wait {remaining_seconds} seconds "
                f"before submitting another round."
            )

    async def _enforce_pending_round_limit(self, session_id: UUID) -> None:
        if self._policy.max_pending_rounds is None:
            return
        pending_rounds = await self._order_repository.count_pending_rounds(
            session_id,
        )
        if pending_rounds >= self._policy.max_pending_rounds:
            raise MaxPendingRoundsExceededError(
                f"Session {session_id} already has {pending_rounds} rounds "
                f"waiting in the kitchen but the policy allows at most "
                f"{self._policy.max_pending_rounds}."
            )
