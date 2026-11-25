"""Domain exceptions describing business rule violations in plain Python terms."""

class DomainError(Exception):
    """Base class for every error raised by the pure buffet ordering core."""


class InvalidDomainValueError(DomainError):
    """Raised when an entity attribute fails its intrinsic validation."""


class InvalidDinerIdentifierError(DomainError):
    """Raised when a diner identifier is not a valid uppercase A-Z letter."""


class InvalidRestaurantPolicyError(DomainError):
    """Raised when restaurant policy limits are inconsistent or out of range."""


class GuestCapacityExceededError(DomainError):
    """Raised when more diners join a session than its guest count allows."""


class SessionNotActiveError(DomainError):
    """Raised when an operation requires an open session but the session is closed."""


class EmptyOrderRoundError(DomainError):
    """Raised when an order round is submitted without any cart items."""


class RoundAlreadyCompletedError(DomainError):
    """Raised when completing a round that is no longer pending in the kitchen."""


class DishLimitExceededError(DomainError):
    """Raised when a round breaks the per-guest dish limit of the restaurant policy."""


class RoundCooldownNotElapsedError(DomainError):
    """Raised when a round is submitted before the policy cooldown elapsed."""


class MaxPendingRoundsExceededError(DomainError):
    """Raised when a session reaches the pending kitchen rounds allowed by policy."""


class ConcurrentModificationError(DomainError):
    """Raised when concurrent writers invalidate state computed by a use case."""
