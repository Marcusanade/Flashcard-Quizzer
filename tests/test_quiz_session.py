"""Unit tests for ``QuizSession``, ``is_correct_answer`` and the stats classes."""

from collections.abc import Callable, Sequence
from dataclasses import FrozenInstanceError

import pytest

from models import Flashcard
from quiz_engine import (
    AdaptiveMode,
    AnswerResult,
    QuizMode,
    QuizModeFactory,
    QuizSession,
    SequentialMode,
    SessionStats,
    is_correct_answer,
)
from tests.helpers import make_cards


class RecordingMode(QuizMode):
    """Mode that returns the cards in order and stores every reported result."""

    def __init__(self, cards: Sequence[Flashcard]) -> None:
        """Keep a queue of cards and an empty list of recorded results."""
        super().__init__(cards)
        self._queue = list(cards)
        self.recorded: list[tuple[Flashcard, bool]] = []

    def next_card(self) -> Flashcard | None:
        """Return the next card in order."""
        return self._queue.pop(0) if self._queue else None

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Store the reported pair."""
        self.recorded.append((card, correct))


def play(session: QuizSession, results: Sequence[bool]) -> list[str]:
    """Answer one question per scripted result and return the fronts asked."""
    fronts: list[str] = []
    for result in results:
        card = session.next_question()
        assert card is not None
        session.submit_answer(card.back if result else "wrong")
        fronts.append(card.front)
    return fronts


def build_adaptive_via_factory(cards: list[Flashcard]) -> QuizMode:
    """Build an adaptive mode with the factory (default rest)."""
    return QuizModeFactory.create_mode("adaptive", cards)


def build_adaptive_directly(cards: list[Flashcard]) -> QuizMode:
    """Build an adaptive mode directly with rest=2."""
    return AdaptiveMode(cards, rest=2)


# --- is_correct_answer -------------------------------------------------------


@pytest.mark.parametrize(
    ("given", "expected", "result"),
    [
        (" Hello ", "hello", True),
        ("HELLO", "hello", True),
        ("hello", "  Hello  ", True),
        ("", "a", False),
        ("   ", "   ", False),
        ("", "", False),
        ("a  b", "a b", False),
        ("a b", "a b", True),
        # This case needs casefold(): lower() would keep the "ß".
        ("Straße", "STRASSE", True),
    ],
    ids=[
        "spaces-ignored",
        "uppercase-given",
        "spaces-and-case-in-expected",
        "empty-given",
        "blank-both",
        "empty-both",
        "inner-spaces-not-collapsed",
        "same-inner-spaces",
        "casefold-sharp-s",
    ],
)
def test_is_correct_answer(given: str, expected: str, result: bool) -> None:
    assert is_correct_answer(given, expected) is result


# --- AnswerResult and SessionStats -------------------------------------------


def test_answer_result_is_frozen() -> None:
    result = AnswerResult(correct=True, expected="a")

    with pytest.raises(FrozenInstanceError):
        setattr(result, "correct", False)


def test_session_stats_is_frozen() -> None:
    stats = SessionStats(total_questions=1, correct_answers=1, missed_terms=())

    with pytest.raises(FrozenInstanceError):
        setattr(stats, "total_questions", 2)


@pytest.mark.parametrize(
    ("total", "correct", "expected"),
    [(0, 0, 0.0), (4, 4, 100.0), (3, 2, 66.67)],
    ids=["no-questions", "all-correct", "two-of-three"],
)
def test_session_stats_accuracy_percent(
    total: int, correct: int, expected: float
) -> None:
    stats = SessionStats(
        total_questions=total, correct_answers=correct, missed_terms=()
    )

    assert stats.accuracy_percent == pytest.approx(expected, abs=0.01)


# --- QuizSession: statistics -------------------------------------------------


def test_session_sequential_stats_and_results() -> None:
    session = QuizSession(SequentialMode(make_cards("A", "B", "C")))
    results: list[AnswerResult] = []

    for answer in ("a", "x", "C"):
        assert session.next_question() is not None
        results.append(session.submit_answer(answer))
    stats = session.stats()

    assert results == [
        AnswerResult(correct=True, expected="a"),
        AnswerResult(correct=False, expected="b"),
        AnswerResult(correct=True, expected="c"),
    ]
    assert stats.total_questions == 3
    assert stats.correct_answers == 2
    assert stats.accuracy_percent == pytest.approx(66.67, abs=0.01)
    assert stats.missed_terms == ("B",)


@pytest.mark.parametrize(
    "build_mode",
    [build_adaptive_via_factory, build_adaptive_directly],
    ids=["factory-default-rest", "direct-rest-2"],
)
def test_session_adaptive_repeats_failed_cards(
    build_mode: Callable[[list[Flashcard]], QuizMode],
) -> None:
    session = QuizSession(build_mode(make_cards("A", "B", "C", "D", "E")))

    fronts = play(session, [True, False, True, True, False, True, False])
    stats = session.stats()

    assert fronts == ["A", "B", "C", "D", "B", "E", "B"]
    assert session.next_question() is None
    assert stats.total_questions == 7
    assert stats.correct_answers == 4
    assert stats.accuracy_percent == pytest.approx(57.14, abs=0.01)
    assert stats.missed_terms == ("B",)


@pytest.mark.parametrize(
    ("fronts", "expected"),
    [
        (("A", "B", "C"), ("A", "B", "C")),
        (("C", "A", "B"), ("C", "A", "B")),
    ],
    ids=["abc", "cab"],
)
def test_session_missed_terms_keep_order_of_first_miss(
    fronts: tuple[str, ...], expected: tuple[str, ...]
) -> None:
    session = QuizSession(SequentialMode(make_cards(*fronts)))

    play(session, [False] * 3)

    assert session.stats().missed_terms == expected


def test_session_identical_cards_count_as_one_missed_term() -> None:
    # Identical cards are the same term, so the term appears only once.
    cards = [Flashcard(front="Q", back="a"), Flashcard(front="Q", back="a")]
    session = QuizSession(SequentialMode(cards))

    play(session, [False, False])
    stats = session.stats()

    assert stats.total_questions == 2
    assert stats.missed_terms == ("Q",)


def test_session_without_answers_has_empty_stats() -> None:
    session = QuizSession(SequentialMode(make_cards("A", "B")))

    stats = session.stats()

    assert stats.total_questions == 0
    assert stats.correct_answers == 0
    assert stats.accuracy_percent == 0.0
    assert stats.missed_terms == ()


def test_session_unanswered_question_is_not_counted() -> None:
    session = QuizSession(SequentialMode(make_cards("A", "B", "C")))
    session.next_question()
    session.submit_answer("a")
    session.next_question()

    stats = session.stats()

    assert stats.total_questions == 1


# --- QuizSession: errors -----------------------------------------------------


def test_session_submit_answer_without_question_raises() -> None:
    session = QuizSession(SequentialMode(make_cards("A")))

    with pytest.raises(ValueError, match="no question waiting"):
        session.submit_answer("a")


def test_session_next_question_twice_without_answer_raises() -> None:
    session = QuizSession(SequentialMode(make_cards("A", "B")))
    session.next_question()

    with pytest.raises(ValueError, match="not been answered"):
        session.next_question()


def test_session_submit_answer_after_the_end_raises() -> None:
    session = QuizSession(SequentialMode(make_cards("A")))
    session.next_question()
    session.submit_answer("a")
    assert session.next_question() is None

    with pytest.raises(ValueError, match="no question waiting"):
        session.submit_answer("a")


# --- QuizSession and the mode ------------------------------------------------


def test_session_reports_every_outcome_to_the_mode() -> None:
    cards = make_cards("A", "B", "C")
    mode = RecordingMode(cards)
    session = QuizSession(mode)

    for answer in ("a", "x", "c"):
        assert session.next_question() is not None
        session.submit_answer(answer)

    assert [correct for _, correct in mode.recorded] == [True, False, True]
    assert all(
        recorded is original for (recorded, _), original in zip(mode.recorded, cards)
    )
    assert len(mode.recorded) == 3
