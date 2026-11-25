"""CartItem entity: one dish line added to the shared table cart by a diner."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.exceptions import InvalidDomainValueError
from app.domain.value_objects import DinerIdentifier


@dataclass(frozen=True, slots=True, kw_only=True)
class CartItem:
    """Immutable line of the shared cart attributing a dish to a single diner.

    Items accumulate in the shared cart until a diner submits them as part of
    an order round; the diner identifier keeps every line attributable to the
    guest who asked for it.
    """

    item_id: UUID = field(default_factory=uuid4)
    session_id: UUID
    diner_identifier: DinerIdentifier
    dish_id: UUID
    dish_name: str
    station: str
    quantity: int
    added_at: datetime

    def __post_init__(self) -> None:
        if not self.dish_name.strip():
            raise InvalidDomainValueError("dish_name must not be empty.")
        if not self.station.strip():
            raise InvalidDomainValueError("station must not be empty.")
        if self.quantity < 1:
            raise InvalidDomainValueError(
                f"quantity must be a positive integer, got {self.quantity}."
            )
