"""Value objects encoding the intrinsic invariants shared by domain entities."""

import re
from dataclasses import dataclass

from app.domain.exceptions import InvalidDinerIdentifierError

DINER_IDENTIFIER_PATTERN = re.compile(r"^[A-Z]$")
MAX_DINER_IDENTIFIERS = 26


@dataclass(frozen=True, slots=True)
class DinerIdentifier:
    """Uppercase letter attributing shared cart items to one diner at a table.

    Diners at the same table are addressed sequentially (A, B, C...) so every
    line of the shared cart stays attributable in the kitchen ticket and the
    real-time cart view.
    """

    letter: str

    def __post_init__(self) -> None:
        if not DINER_IDENTIFIER_PATTERN.match(self.letter):
            raise InvalidDinerIdentifierError(
                "Diner identifier must be a single uppercase letter, "
                f"got {self.letter!r}."
            )

    @classmethod
    def from_sequence(cls, position: int) -> "DinerIdentifier":
        """Maps a zero-based seat position to its sequential letter (0 -> A)."""
        if not 0 <= position < MAX_DINER_IDENTIFIERS:
            raise InvalidDinerIdentifierError(
                f"Seat position {position} is outside the A-Z diner alphabet."
            )
        return cls(chr(ord("A") + position))

    def __str__(self) -> str:
        return self.letter
