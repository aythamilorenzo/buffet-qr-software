"""Unit tests for OrderRound batch invariants and the kitchen lifecycle."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.cart_item import CartItem
from app.domain.exceptions import (
    EmptyOrderRoundError,
    InvalidDomainValueError,
    RoundAlreadyCompletedError,
)
from app.domain.order_round import OrderRound, RoundStatus
from app.domain.value_objects import DinerIdentifier

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 25, 12, 10, tzinfo=UTC)
SESSION_ID = uuid4()
OTHER_SESSION_ID = uuid4()


def build_cart_item(
    diner_letter: str = "A",
    quantity: int = 2,
    session_id: UUID = SESSION_ID,
) -> CartItem:
    return CartItem(
        session_id=session_id,
        diner_identifier=DinerIdentifier(diner_letter),
        dish_id=uuid4(),
        dish_name="California Roll",
        station="sushi",
        quantity=quantity,
        added_at=NOW,
    )


def build_round(
    items: tuple[CartItem, ...] | None = None,
    round_number: int = 1,
) -> OrderRound:
    return OrderRound(
        session_id=SESSION_ID,
        round_number=round_number,
        items=items if items is not None else (build_cart_item(),),
        submitted_by=DinerIdentifier("A"),
        submitted_at=NOW,
    )


def test_round_requires_at_least_one_cart_item() -> None:
    with pytest.raises(EmptyOrderRoundError):
        build_round(items=())


def test_round_rejects_non_positive_round_number() -> None:
    with pytest.raises(InvalidDomainValueError):
        build_round(round_number=0)


def test_round_rejects_items_belonging_to_another_session() -> None:
    foreign_item = build_cart_item(session_id=OTHER_SESSION_ID)
    with pytest.raises(InvalidDomainValueError):
        build_round(items=(foreign_item,))


def test_round_starts_pending_without_completion_timestamp() -> None:
    round_ = build_round()
    assert round_.status is RoundStatus.PENDING
    assert round_.completed_at is None


def test_mark_completed_returns_the_completed_round() -> None:
    completed_round = build_round().mark_completed(LATER)
    assert completed_round.status is RoundStatus.COMPLETED
    assert completed_round.completed_at == LATER
    assert build_round().status is RoundStatus.PENDING


def test_mark_completed_rejects_an_already_completed_round() -> None:
    completed_round = build_round().mark_completed(LATER)
    with pytest.raises(RoundAlreadyCompletedError):
        completed_round.mark_completed(LATER)


def test_pending_round_must_not_carry_a_completion_timestamp() -> None:
    with pytest.raises(InvalidDomainValueError):
        OrderRound(
            session_id=SESSION_ID,
            round_number=1,
            items=(build_cart_item(),),
            submitted_by=DinerIdentifier("A"),
            submitted_at=NOW,
            completed_at=LATER,
        )


def test_completed_round_requires_a_completion_timestamp() -> None:
    with pytest.raises(InvalidDomainValueError):
        OrderRound(
            session_id=SESSION_ID,
            round_number=1,
            items=(build_cart_item(),),
            submitted_by=DinerIdentifier("A"),
            submitted_at=NOW,
            status=RoundStatus.COMPLETED,
        )


def test_total_dish_quantity_sums_every_cart_line() -> None:
    items = (build_cart_item(quantity=2), build_cart_item(quantity=3))
    assert build_round(items=items).total_dish_quantity == 5


def test_dish_quantity_per_diner_groups_lines_by_identifier() -> None:
    items = (
        build_cart_item(diner_letter="A", quantity=2),
        build_cart_item(diner_letter="B", quantity=1),
        build_cart_item(diner_letter="A", quantity=3),
    )
    assert build_round(items=items).dish_quantity_per_diner() == {
        DinerIdentifier("A"): 5,
        DinerIdentifier("B"): 1,
    }
