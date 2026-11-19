"""Unit tests for the quiz modes and for ``QuizModeFactory``."""

import inspect
import random
import re
from collections.abc import Callable, Sequence
from typing import cast

import pytest

from models import Flashcard
from quiz_engine import (
    AdaptiveMode,
    QuizMode,
    QuizModeFactory,
    RandomMode,
    SequentialMode,
    rest_for_deck_size,
)

MODE_NAMES = ["sequential", "random", "adaptive"]


def make_cards(*fronts: str) -> list[Flashcard]:
    """Build cards whose back is the front in lowercase."""
    return [Flashcard(front=front, back=front.lower()) for front in fronts]


def ask_questions(mode: QuizMode, results: Sequence[bool]) -> list[str]:
    """Ask one question per scripted result, report it and return the fronts."""
    fronts: list[str] = []
    for result in results:
        card = mode.next_card()
        assert card is not None
        mode.record_result(card, result)
        fronts.append(card.front)
    return fronts


def assert_finished(mode: QuizMode) -> None:
    """Assert that the mode has no more cards."""
    assert mode.next_card() is None


def make_sequential(cards: list[Flashcard]) -> QuizMode:
    """Build a sequential mode."""
    return SequentialMode(cards)


def make_seeded_random(cards: list[Flashcard]) -> QuizMode:
    """Build a random mode with a fixed seed."""
    return RandomMode(cards, random.Random(3))


class ReverseMode(QuizMode):
    """Small extra mode used to test the extensibility of the factory."""

    def __init__(self, cards: Sequence[Flashcard]) -> None:
        """Keep the cards in reverse order."""
        super().__init__(cards)
        self._remaining = list(reversed(cards))

    def next_card(self) -> Flashcard | None:
        """Return the last card of the deck first."""
        return self._remaining.pop(0) if self._remaining else None


# --- QuizMode (abstract class) -----------------------------------------------


def test_quiz_mode_is_abstract_with_only_next_card_abstract() -> None:
    assert inspect.isabstract(QuizMode)
    assert QuizMode.__abstractmethods__ == frozenset({"next_card"})


def test_quiz_mode_cannot_be_instantiated() -> None:
    abstract_class = cast(Callable[..., QuizMode], QuizMode)

    with pytest.raises(TypeError):
        abstract_class(make_cards("A"))


# --- Behaviors shared by the three modes -------------------------------------


@pytest.mark.parametrize("name", MODE_NAMES)
def test_mode_empty_deck_raises_value_error(name: str) -> None:
    with pytest.raises(ValueError, match="at least one card"):
        QuizModeFactory.create_mode(name, [])


@pytest.mark.parametrize("name", MODE_NAMES)
def test_mode_keeps_its_own_copy_of_the_cards(name: str) -> None:
    cards = make_cards("A", "B", "C")
    mode = QuizModeFactory.create_mode(name, cards)

    cards.append(Flashcard(front="D", back="d"))
    fronts = ask_questions(mode, [True] * 3)

    assert len(fronts) == 3
    assert_finished(mode)


@pytest.mark.parametrize("name", MODE_NAMES)
def test_mode_keeps_returning_none_after_the_end(name: str) -> None:
    mode = QuizModeFactory.create_mode(name, make_cards("A", "B"))
    ask_questions(mode, [True, True])

    first = mode.next_card()
    second = mode.next_card()

    assert first is None
    assert second is None


@pytest.mark.parametrize(
    "make_mode",
    [make_sequential, make_seeded_random],
    ids=["sequential", "random"],
)
def test_mode_record_result_is_a_no_op_for_sequential_and_random(
    make_mode: Callable[[list[Flashcard]], QuizMode],
) -> None:
    cards = make_cards("A", "B", "C", "D")
    fresh = make_mode(cards)
    scripted = make_mode(cards)

    expected = ask_questions(fresh, [True] * 4)
    actual = ask_questions(scripted, [False, True, False, True])

    assert actual == expected


# --- QuizModeFactory ---------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected_class"),
    [
        ("sequential", SequentialMode),
        ("random", RandomMode),
        ("adaptive", AdaptiveMode),
        ("  Adaptive ", AdaptiveMode),
        ("RANDOM", RandomMode),
        ("Sequential ", SequentialMode),
    ],
    ids=[
        "sequential",
        "random",
        "adaptive",
        "adaptive-with-spaces",
        "random-uppercase",
        "sequential-trailing-space",
    ],
)
def test_quiz_mode_factory(name: str, expected_class: type[QuizMode]) -> None:
    mode = QuizModeFactory.create_mode(name, make_cards("A", "B"))

    assert type(mode) is expected_class


@pytest.mark.parametrize("name", MODE_NAMES)
def test_factory_every_call_returns_a_new_object(name: str) -> None:
    cards = make_cards("A", "B")

    first = QuizModeFactory.create_mode(name, cards)
    second = QuizModeFactory.create_mode(name, cards)

    assert first is not second


def test_factory_instances_are_independent() -> None:
    cards = make_cards("A", "B", "C")
    first = QuizModeFactory.create_mode("sequential", cards)
    second = QuizModeFactory.create_mode("sequential", cards)

    first.next_card()
    first.next_card()

    assert second.next_card() == cards[0]


def test_factory_unknown_name_message() -> None:
    expected = (
        "Unknown quiz mode: 'foo'. Available modes: adaptive, random, sequential."
    )

    with pytest.raises(ValueError, match=re.escape(expected)) as info:
        QuizModeFactory.create_mode("foo", make_cards("A"))

    assert "\n" not in str(info.value)


def test_factory_unknown_name_is_shown_stripped() -> None:
    with pytest.raises(ValueError, match=re.escape("Unknown quiz mode: 'Foo'.")):
        QuizModeFactory.create_mode(" Foo ", make_cards("A"))


def test_factory_empty_name_raises_value_error() -> None:
    with pytest.raises(ValueError, match=re.escape("Unknown quiz mode: ''.")):
        QuizModeFactory.create_mode("", make_cards("A"))


def test_factory_available_modes_are_sorted_tuple() -> None:
    modes = QuizModeFactory.available_modes()

    assert modes == ("adaptive", "random", "sequential")
    assert isinstance(modes, tuple)


def test_factory_empty_deck_raises_value_error() -> None:
    with pytest.raises(ValueError, match="at least one card"):
        QuizModeFactory.create_mode("sequential", [])


def test_factory_accepts_a_new_mode_with_one_registry_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # This is the only test that touches the private registry. It shows that a
    # new mode needs just one class and one registry entry.
    monkeypatch.setitem(QuizModeFactory._registry, "reverse", ReverseMode)
    cards = make_cards("A", "B", "C")

    mode = QuizModeFactory.create_mode("reverse", cards)

    assert isinstance(mode, ReverseMode)
    assert ask_questions(mode, [True] * 3) == ["C", "B", "A"]
    assert "reverse" in QuizModeFactory.available_modes()


# --- SequentialMode ----------------------------------------------------------


def test_sequential_mode_returns_cards_in_file_order() -> None:
    mode = SequentialMode(make_cards("C", "A", "B"))

    fronts = ask_questions(mode, [True] * 3)

    assert fronts == ["C", "A", "B"]
    assert_finished(mode)


def test_sequential_mode_single_card_deck() -> None:
    mode = SequentialMode(make_cards("A"))

    fronts = ask_questions(mode, [True])

    assert fronts == ["A"]
    assert_finished(mode)


# --- RandomMode --------------------------------------------------------------


def test_random_mode_asks_every_card_exactly_once() -> None:
    cards = make_cards("A", "B", "C", "D", "E")
    mode = RandomMode(cards, random.Random(0))

    fronts = ask_questions(mode, [True] * 5)

    assert sorted(fronts) == ["A", "B", "C", "D", "E"]
    assert_finished(mode)


def test_random_mode_same_seed_gives_same_order() -> None:
    cards = make_cards(*"ABCDEFGHIJ")
    first = RandomMode(cards, random.Random(7))
    second = RandomMode(cards, random.Random(7))

    assert ask_questions(first, [True] * 10) == ask_questions(second, [True] * 10)


def test_random_mode_can_differ_from_file_order() -> None:
    fronts_in_file = list("ABCDEFGHIJ")
    cards = make_cards(*fronts_in_file)

    orders = [
        ask_questions(RandomMode(cards, random.Random(seed)), [True] * 10)
        for seed in range(20)
    ]

    assert any(order != fronts_in_file for order in orders)


def test_random_mode_does_not_use_the_global_random_state() -> None:
    cards = make_cards(*"ABCDEFGHIJ")
    random.seed(111)
    first = RandomMode(cards, random.Random(1))
    random.seed(222)
    second = RandomMode(cards, random.Random(1))

    assert ask_questions(first, [True] * 10) == ask_questions(second, [True] * 10)


def test_random_mode_works_without_rng_argument() -> None:
    mode = RandomMode(make_cards("A", "B", "C"))

    fronts = ask_questions(mode, [True] * 3)

    assert sorted(fronts) == ["A", "B", "C"]
    assert_finished(mode)


def test_random_mode_asks_both_identical_cards() -> None:
    cards = [Flashcard(front="Q", back="a"), Flashcard(front="Q", back="a")]
    mode = RandomMode(cards, random.Random(0))

    fronts = ask_questions(mode, [True, True])

    assert fronts == ["Q", "Q"]
    assert_finished(mode)


# --- rest_for_deck_size ------------------------------------------------------


@pytest.mark.parametrize(
    ("deck_size", "expected"),
    [
        (0, 2),
        (1, 2),
        (10, 2),
        (20, 2),
        (29, 2),
        (30, 3),
        (50, 5),
        (100, 10),
        (150, 10),
        (200, 10),
    ],
)
def test_rest_for_deck_size(deck_size: int, expected: int) -> None:
    assert rest_for_deck_size(deck_size) == expected


# --- AdaptiveMode ------------------------------------------------------------


def test_adaptive_mode_behavior() -> None:
    mode = AdaptiveMode(make_cards("A", "B", "C", "D", "E"), rest=2, max_failures=3)

    fronts = ask_questions(mode, [True, False, True, True, False, True, False])

    assert fronts == ["A", "B", "C", "D", "B", "E", "B"]
    assert_finished(mode)


def test_adaptive_mode_review_card_goes_before_next_unseen_card() -> None:
    mode = AdaptiveMode(make_cards("A", "B", "C", "D"), rest=1)

    fronts = ask_questions(mode, [False, True, True, True, True])

    assert fronts == ["A", "B", "A", "C", "D"]
    assert_finished(mode)


def test_adaptive_mode_only_card_is_served_even_while_resting() -> None:
    mode = AdaptiveMode(make_cards("A"), rest=2)

    fronts = ask_questions(mode, [False, False, False])

    assert fronts == ["A", "A", "A"]
    assert_finished(mode)


def test_adaptive_mode_retires_card_at_first_failure_when_max_is_one() -> None:
    mode = AdaptiveMode(make_cards("A", "B"), max_failures=1)

    fronts = ask_questions(mode, [False, True])

    assert fronts == ["A", "B"]
    assert_finished(mode)


def test_adaptive_mode_retires_card_after_max_failures() -> None:
    mode = AdaptiveMode(make_cards("A"), max_failures=2)

    fronts = ask_questions(mode, [False, False])

    assert fronts == ["A", "A"]
    assert_finished(mode)


def test_adaptive_mode_correct_answer_on_repeat_removes_the_card() -> None:
    mode = AdaptiveMode(make_cards("A", "B"), rest=2)

    fronts = ask_questions(mode, [False, True, True])

    assert fronts == ["A", "B", "A"]
    assert_finished(mode)


def test_adaptive_mode_does_not_repeat_a_card_immediately() -> None:
    mode = AdaptiveMode(make_cards("A", "B"), rest=0)

    fronts = ask_questions(mode, [False, True, False, False])

    # After the first failure of A the next card is B and not A, even though
    # its rest is 0. The last A is repeated only because it is the only card
    # left.
    assert fronts == ["A", "B", "A", "A"]
    assert_finished(mode)


def test_adaptive_mode_default_rest_for_ten_card_deck() -> None:
    mode = AdaptiveMode(make_cards(*[f"Q{i}" for i in range(10)]))

    fronts = ask_questions(mode, [False, True, True, True, True])

    assert fronts == ["Q0", "Q1", "Q2", "Q0", "Q3"]


def test_adaptive_mode_default_rest_for_fifty_card_deck() -> None:
    mode = AdaptiveMode(make_cards(*[f"Q{i}" for i in range(50)]))

    fronts = ask_questions(mode, [False] + [True] * 7)

    assert fronts == ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q0", "Q6"]


def test_adaptive_mode_identical_cards_keep_separate_counters() -> None:
    cards = [Flashcard(front="Q", back="a"), Flashcard(front="Q", back="a")]
    mode = AdaptiveMode(cards, rest=2, max_failures=2)

    fronts = ask_questions(mode, [False, False, False, False])

    # A counter shared by value would retire the card after two failures in
    # total, so only two questions would be asked.
    assert len(fronts) == 4
    assert_finished(mode)


def test_adaptive_mode_is_deterministic() -> None:
    cards = make_cards("A", "B", "C", "D", "E")
    results = [False, True, False, True, True, False, True]
    first = AdaptiveMode(cards, rest=2)
    second = AdaptiveMode(cards, rest=2)

    assert ask_questions(first, results) == ask_questions(second, results)


def test_adaptive_mode_record_result_before_any_question_raises() -> None:
    cards = make_cards("A", "B")
    mode = AdaptiveMode(cards)

    with pytest.raises(ValueError, match="no served card"):
        mode.record_result(cards[0], True)


def test_adaptive_mode_record_result_with_another_card_raises() -> None:
    mode = AdaptiveMode(make_cards("A", "B"))
    mode.next_card()

    with pytest.raises(ValueError, match="not the one"):
        mode.record_result(Flashcard(front="Z", back="z"), True)


def test_adaptive_mode_record_result_twice_for_same_question_raises() -> None:
    mode = AdaptiveMode(make_cards("A", "B"))
    card = mode.next_card()
    assert card is not None
    mode.record_result(card, True)

    with pytest.raises(ValueError, match="no served card"):
        mode.record_result(card, True)


@pytest.mark.parametrize("max_failures", [0, -1])
def test_adaptive_mode_invalid_max_failures_raises(max_failures: int) -> None:
    with pytest.raises(ValueError, match="max_failures must be at least 1"):
        AdaptiveMode(make_cards("A"), max_failures=max_failures)


def test_adaptive_mode_negative_rest_raises() -> None:
    with pytest.raises(ValueError, match="rest must not be negative"):
        AdaptiveMode(make_cards("A"), rest=-1)


def test_adaptive_mode_rest_zero_is_allowed() -> None:
    mode = AdaptiveMode(make_cards("A"), rest=0)

    assert mode.next_card() == Flashcard(front="A", back="a")


def test_adaptive_mode_empty_deck_error_comes_first() -> None:
    with pytest.raises(ValueError, match="at least one card"):
        AdaptiveMode([], max_failures=0)
