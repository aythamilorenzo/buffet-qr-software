"""Pure domain layer: entities, value objects and business rules in plain Python."""

from app.domain.cart_item import CartItem
from app.domain.exceptions import (
    ConcurrentModificationError,
    DinerNotAssignedToSessionError,
    DishLimitExceededError,
    DomainError,
    EmptyOrderRoundError,
    GuestCapacityExceededError,
    InvalidDinerIdentifierError,
    InvalidDomainValueError,
    InvalidRestaurantPolicyError,
    MaxDinersPerTableExceededError,
    MaxPendingRoundsExceededError,
    RoundAlreadyCompletedError,
    RoundCooldownNotElapsedError,
    SessionNotActiveError,
    TableSessionAlreadyActiveError,
    TableSessionNotFoundError,
)
from app.domain.order_round import OrderRound, RoundStatus
from app.domain.restaurant_policy import RestaurantPolicy
from app.domain.table_session import SessionStatus, TableSession
from app.domain.value_objects import DinerIdentifier

__all__ = [
    "CartItem",
    "ConcurrentModificationError",
    "DinerIdentifier",
    "DinerNotAssignedToSessionError",
    "DishLimitExceededError",
    "DomainError",
    "EmptyOrderRoundError",
    "GuestCapacityExceededError",
    "InvalidDomainValueError",
    "InvalidDinerIdentifierError",
    "InvalidRestaurantPolicyError",
    "MaxDinersPerTableExceededError",
    "MaxPendingRoundsExceededError",
    "OrderRound",
    "RestaurantPolicy",
    "RoundAlreadyCompletedError",
    "RoundCooldownNotElapsedError",
    "RoundStatus",
    "SessionNotActiveError",
    "SessionStatus",
    "TableSession",
    "TableSessionAlreadyActiveError",
    "TableSessionNotFoundError",
]
