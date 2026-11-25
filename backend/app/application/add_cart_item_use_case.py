"""Use case that adds one dish line to the shared cart of an open session."""

from datetime import datetime
from uuid import UUID

from app.domain.cart_item import CartItem
from app.domain.exceptions import (
    DinerNotAssignedToSessionError,
    SessionNotActiveError,
    TableSessionNotFoundError,
)
from app.domain.value_objects import DinerIdentifier
from app.ports.order_repository import OrderRepositoryPort
from app.ports.session_repository import SessionRepositoryPort


class AddCartItemUseCase:
    """Attributes a dish to a seated diner inside the shared table cart.

    The session must be open and the diner letter must belong to the seats
    assigned by the waiter, so stale or forged identifiers never reach the
    kitchen ticket. Policy limits are enforced later, at round submission.
    """

    def __init__(
        self,
        session_repository: SessionRepositoryPort,
        order_repository: OrderRepositoryPort,
    ) -> None:
        self._session_repository = session_repository
        self._order_repository = order_repository

    async def execute(
        self,
        session_id: UUID,
        diner_identifier: DinerIdentifier,
        dish_id: UUID,
        dish_name: str,
        station: str,
        quantity: int,
        added_at: datetime,
    ) -> CartItem:
        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise TableSessionNotFoundError(
                f"Table session {session_id} does not exist."
            )
        if not session.is_open:
            raise SessionNotActiveError(
                f"Session {session_id} is closed and no longer accepts orders."
            )
        if diner_identifier not in session.assigned_identifiers:
            raise DinerNotAssignedToSessionError(
                f"Diner {diner_identifier} was never seated at session "
                f"{session_id}."
            )
        item = CartItem(
            session_id=session_id,
            diner_identifier=diner_identifier,
            dish_id=dish_id,
            dish_name=dish_name,
            station=station,
            quantity=quantity,
            added_at=added_at,
        )
        await self._order_repository.save_cart_item(item)
        return item
