"""Unit tests for the DinerIdentifier value object."""

import pytest

from app.domain.exceptions import InvalidDinerIdentifierError
from app.domain.value_objects import DinerIdentifier


@pytest.mark.parametrize("letter", ["A", "M", "Z"])
def test_diner_identifier_accepts_single_uppercase_letters(letter: str) -> None:
    assert DinerIdentifier(letter).letter == letter


@pytest.mark.parametrize("letter", ["a", "AA", "1", "", " B", "B "])
def test_diner_identifier_rejects_malformed_letters(letter: str) -> None:
    with pytest.raises(InvalidDinerIdentifierError):
        DinerIdentifier(letter)


def test_diner_identifier_string_returns_the_letter() -> None:
    assert str(DinerIdentifier("C")) == "C"


def test_from_sequence_maps_seat_positions_to_letters() -> None:
    assert DinerIdentifier.from_sequence(0) == DinerIdentifier("A")
    assert DinerIdentifier.from_sequence(25) == DinerIdentifier("Z")


@pytest.mark.parametrize("position", [-1, 26, 100])
def test_from_sequence_rejects_positions_outside_the_alphabet(
    position: int,
) -> None:
    with pytest.raises(InvalidDinerIdentifierError):
        DinerIdentifier.from_sequence(position)
