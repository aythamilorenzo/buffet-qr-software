"""Unit tests for CartItem invariants of the shared table cart."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.cart_item import CartItem
from app.domain.exceptions import InvalidDomainValueError
from app.domain.value_objects import DinerIdentifier

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
SESSION_ID = uuid4()


def build_cart_item(
    quantity: int = 2,
    dish_name: str = "California Roll",
    station: str = "sushi",
    session_id: UUID = SESSION_ID,
) -> CartItem:
    return CartItem(
        session_id=session_id,
        diner_identifier=DinerIdentifier("A"),
        dish_id=uuid4(),
        dish_name=dish_name,
        station=station,
        quantity=quantity,
        added_at=NOW,
    )


def test_each_construction_generates_a_fresh_item_id() -> None:
    assert build_cart_item().item_id != build_cart_item().item_id


def test_cart_item_accepts_positive_quantity() -> None:
    assert build_cart_item(quantity=3).quantity == 3


@pytest.mark.parametrize("quantity", [0, -2])
def test_cart_item_rejects_non_positive_quantity(quantity: int) -> None:
    with pytest.raises(InvalidDomainValueError):
        build_cart_item(quantity=quantity)


@pytest.mark.parametrize("dish_name", ["", "   "])
def test_cart_item_rejects_empty_dish_name(dish_name: str) -> None:
    with pytest.raises(InvalidDomainValueError):
        build_cart_item(dish_name=dish_name)


@pytest.mark.parametrize("station", ["", "   "])
def test_cart_item_rejects_empty_station(station: str) -> None:
    with pytest.raises(InvalidDomainValueError):
        build_cart_item(station=station)
