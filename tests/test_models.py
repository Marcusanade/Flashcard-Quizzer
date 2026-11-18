"""Unit tests for the ``Flashcard`` model."""

from dataclasses import FrozenInstanceError

import pytest

from models import Flashcard


@pytest.mark.parametrize("field", ["front", "back"])
def test_flashcard_is_frozen(field: str) -> None:
    card = Flashcard(front="A", back="B")

    with pytest.raises(FrozenInstanceError):
        setattr(card, field, "x")


def test_flashcard_equal_when_texts_match() -> None:
    first = Flashcard(front="A", back="B")
    second = Flashcard(front="A", back="B")

    assert first == second


@pytest.mark.parametrize(
    ("other_front", "other_back"),
    [("X", "B"), ("A", "X")],
    ids=["different-front", "different-back"],
)
def test_flashcard_not_equal_when_a_text_differs(
    other_front: str, other_back: str
) -> None:
    card = Flashcard(front="A", back="B")
    other = Flashcard(front=other_front, back=other_back)

    assert card != other


def test_flashcard_equal_cards_have_same_hash() -> None:
    first = Flashcard(front="A", back="B")
    second = Flashcard(front="A", back="B")

    assert hash(first) == hash(second)


def test_flashcard_can_be_used_as_dictionary_key() -> None:
    key = Flashcard(front="A", back="B")
    scores = {key: 3}

    assert scores[Flashcard(front="A", back="B")] == 3


def test_flashcard_identical_cards_collapse_in_a_set() -> None:
    # Documents the current behavior: duplicate cards are indistinguishable,
    # so a set keeps only one of them.
    cards = {Flashcard(front="A", back="B"), Flashcard(front="A", back="B")}

    assert len(cards) == 1
