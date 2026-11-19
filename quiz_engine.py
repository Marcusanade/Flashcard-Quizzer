"""Quiz logic for the Flashcard Quizzer.

This module uses two design patterns:

* Strategy: ``QuizMode`` and its subclasses decide which flashcard is asked
  next and are interchangeable. ``QuizSession`` is the context that uses one.
* Factory: ``QuizModeFactory`` creates the mode from its name.

This module has no input or output: it knows nothing about the command line
or the screen.

Modes keep state (for example how far through the deck they are), so every
quiz session must create its own new instance.
"""

import random
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

from models import Flashcard


class QuizMode(ABC):
    """Abstract strategy that decides which card is asked next.

    Contract: after each ``next_card()`` call that returns a card, the caller
    reports the outcome with ``record_result()`` using that same card.
    """

    def __init__(self, cards: Sequence[Flashcard]) -> None:
        """Store a private copy of the deck.

        Args:
            cards: The deck, in file order.

        Raises:
            ValueError: If ``cards`` is empty.
        """
        if not cards:
            raise ValueError("A quiz mode needs at least one card.")
        self._cards: tuple[Flashcard, ...] = tuple(cards)

    @abstractmethod
    def next_card(self) -> Flashcard | None:
        """Return the next card to ask.

        Returns:
            The next card, or ``None`` when there are no more cards.
        """

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Report the outcome of the card that was just asked.

        This is a hook: the default implementation does nothing. Modes that
        learn from the answers override it.

        Args:
            card: The card returned by the last ``next_card()`` call.
            correct: Whether the user answered correctly.
        """


class SequentialMode(QuizMode):
    """Ask the cards in file order, one after another."""

    def __init__(self, cards: Sequence[Flashcard]) -> None:
        """Start at the first card.

        Args:
            cards: The deck, in file order.

        Raises:
            ValueError: If ``cards`` is empty.
        """
        super().__init__(cards)
        self._position = 0

    def next_card(self) -> Flashcard | None:
        """Return the next card in file order.

        Returns:
            The next card, or ``None`` after the last one.
        """
        if self._position >= len(self._cards):
            return None
        card = self._cards[self._position]
        self._position += 1
        return card


class RandomMode(QuizMode):
    """Ask every card exactly once, in a random order."""

    def __init__(
        self, cards: Sequence[Flashcard], rng: random.Random | None = None
    ) -> None:
        """Shuffle a copy of the deck once.

        Args:
            cards: The deck, in file order.
            rng: Random generator to use. A new ``random.Random()`` is
                created if it is ``None``. The global random state is never
                used.

        Raises:
            ValueError: If ``cards`` is empty.
        """
        super().__init__(cards)
        generator = rng if rng is not None else random.Random()
        self._order: list[Flashcard] = list(self._cards)
        generator.shuffle(self._order)
        self._position = 0

    def next_card(self) -> Flashcard | None:
        """Return the next card of the shuffled deck.

        Returns:
            The next card, or ``None`` once every card was asked.
        """
        if self._position >= len(self._order):
            return None
        card = self._order[self._position]
        self._position += 1
        return card


def rest_for_deck_size(deck_size: int) -> int:
    """Return how many questions must pass before a failed card comes back.

    The rest grows with the deck so that, in a large deck, a failed card is
    not asked again right after the user has seen its answer.

    Args:
        deck_size: Number of cards in the deck.

    Returns:
        A number between 2 and 10.
    """
    return min(10, max(2, deck_size // 10))


class AdaptiveMode(QuizMode):
    """Prioritize the cards the user got wrong.

    Cards are identified by their position in the deck, so two cards with
    identical text never share a failure counter. A failed card comes back
    after ``rest`` more questions, until it has failed ``max_failures`` times
    and is retired for the rest of the session. The mode is deterministic.
    """

    def __init__(
        self,
        cards: Sequence[Flashcard],
        max_failures: int = 3,
        rest: int | None = None,
    ) -> None:
        """Create the mode.

        Args:
            cards: The deck, in file order.
            max_failures: Failures after which a card is retired.
            rest: Questions that must pass before a failed card comes back.
                Defaults to ``rest_for_deck_size(len(cards))``.

        Raises:
            ValueError: If ``cards`` is empty, ``max_failures`` is less than
                1 or ``rest`` is less than 0.
        """
        super().__init__(cards)
        if max_failures < 1:
            raise ValueError("max_failures must be at least 1.")
        if rest is not None and rest < 0:
            raise ValueError("rest must not be negative.")
        self._max_failures = max_failures
        self._rest = rest if rest is not None else rest_for_deck_size(len(cards))
        self._next_unseen = 0
        self._review: list[tuple[int, int]] = []  # (position, available_at)
        self._failures: dict[int, int] = {}
        self._served = 0
        self._pending: int | None = None
        self._last: int | None = None

    def next_card(self) -> Flashcard | None:
        """Return the next card, giving priority to cards that were failed.

        Order: a review card whose rest has finished, then the next unseen
        card, then the review card that has waited longest even if its rest
        has not finished. A card is not served twice in a row if there is
        another candidate.

        Returns:
            The next card, or ``None`` when no cards are left.
        """
        position = self._take_ready_review()
        if position is None:
            position = self._take_unseen()
        if position is None:
            position = self._take_resting_review()
        if position is None:
            return None
        self._served += 1
        self._pending = position
        self._last = position
        return self._cards[position]

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Apply the outcome to the card that was just served.

        A failed card is scheduled to come back after ``rest`` questions,
        unless it reached ``max_failures`` failures, in which case it is
        retired for the session.

        Args:
            card: The card returned by the last ``next_card()`` call.
            correct: Whether the user answered correctly.

        Raises:
            ValueError: If there is no pending card, or ``card`` is not the
                pending card.
        """
        position = self._pending
        if position is None:
            raise ValueError("There is no served card waiting for a result.")
        if card != self._cards[position]:
            raise ValueError("The card is not the one that was just served.")
        self._pending = None
        if not correct:
            self._register_failure(position)

    def _register_failure(self, position: int) -> None:
        """Count a failure and schedule the card to come back if allowed.

        Args:
            position: Position of the failed card in the deck.
        """
        failures = self._failures.get(position, 0) + 1
        self._failures[position] = failures
        if failures < self._max_failures:
            self._review.append((position, self._served + self._rest))

    def _take_ready_review(self) -> int | None:
        """Take the longest-waiting review card whose rest has finished.

        Returns:
            Its position, or ``None`` if no review card is ready (the card
            served last is skipped).
        """
        ready = [
            entry
            for entry in self._review
            if entry[1] <= self._served and entry[0] != self._last
        ]
        return self._take_earliest(ready)

    def _take_unseen(self) -> int | None:
        """Take the next card that was never served.

        Returns:
            Its position, or ``None`` if every card was served.
        """
        if self._next_unseen >= len(self._cards):
            return None
        position = self._next_unseen
        self._next_unseen += 1
        return position

    def _take_resting_review(self) -> int | None:
        """Take the review card that has waited longest, even if resting.

        The card served last is only chosen if it is the only one left.

        Returns:
            Its position, or ``None`` if the review list is empty.
        """
        others = [entry for entry in self._review if entry[0] != self._last]
        return self._take_earliest(others or self._review)

    def _take_earliest(self, entries: list[tuple[int, int]]) -> int | None:
        """Remove and return the entry with the smallest ``available_at``.

        Args:
            entries: Candidate review entries, all taken from the review list.

        Returns:
            The position of the chosen entry, or ``None`` if there are none.
        """
        if not entries:
            return None
        entry = min(entries, key=lambda item: item[1])
        self._review.remove(entry)
        return entry[0]


class QuizModeFactory:
    """Create quiz modes from their names.

    To add a new mode, write a new ``QuizMode`` subclass and add one entry to
    ``_registry``. Nothing else changes.
    """

    _registry: ClassVar[dict[str, type[QuizMode]]] = {
        "sequential": SequentialMode,
        "random": RandomMode,
        "adaptive": AdaptiveMode,
    }

    @staticmethod
    def create_mode(name: str, cards: Sequence[Flashcard]) -> QuizMode:
        """Create a new mode instance.

        Args:
            name: Name of the mode. Surrounding spaces and letter case are
                ignored.
            cards: The deck, in file order.

        Returns:
            A new mode built with ``cards``. Modes keep state, so every call
            returns a different object.

        Raises:
            ValueError: If the name is unknown or ``cards`` is empty.
        """
        mode_class = QuizModeFactory._registry.get(name.strip().lower())
        if mode_class is None:
            available = ", ".join(QuizModeFactory.available_modes())
            raise ValueError(
                f"Unknown quiz mode: '{name.strip()}'. Available modes: {available}."
            )
        return mode_class(cards)

    @staticmethod
    def available_modes() -> tuple[str, ...]:
        """Return the valid mode names.

        Returns:
            The names, sorted alphabetically.
        """
        return tuple(sorted(QuizModeFactory._registry))


def is_correct_answer(given: str, expected: str) -> bool:
    """Check an answer, ignoring surrounding spaces and letter case.

    Inner spaces are not collapsed. An answer that is empty after ``strip()``
    is always incorrect, whatever the expected text is.

    Args:
        given: The text typed by the user.
        expected: The back of the card.

    Returns:
        True if ``given`` is not empty after ``strip()`` and both strings are
        equal after ``strip()`` and ``casefold()``. False otherwise.
    """
    cleaned = given.strip()
    if not cleaned:
        return False
    return cleaned.casefold() == expected.strip().casefold()


@dataclass(frozen=True)
class AnswerResult:
    """Outcome of one answered question.

    Attributes:
        correct: Whether the answer was correct.
        expected: The back of the card, as stored.
    """

    correct: bool
    expected: str


@dataclass(frozen=True)
class SessionStats:
    """Statistics of a quiz session.

    Attributes:
        total_questions: Questions answered, repetitions included.
        correct_answers: Questions answered correctly.
        missed_terms: Fronts of the cards answered wrongly at least once,
            without duplicates, in order of first miss.
    """

    total_questions: int
    correct_answers: int
    missed_terms: tuple[str, ...]

    @property
    def accuracy_percent(self) -> float:
        """Correct answers as a percentage of the total questions.

        Returns:
            The percentage, or 0.0 if no question was answered.
        """
        if self.total_questions == 0:
            return 0.0
        return 100 * self.correct_answers / self.total_questions


class QuizSession:
    """Context of the Strategy pattern: runs a quiz with one mode.

    The session receives a mode that nobody else uses, because modes keep
    state. It knows nothing about the screen or the keyboard.
    """

    def __init__(self, mode: QuizMode) -> None:
        """Start a session.

        Args:
            mode: The quiz mode that chooses the questions.
        """
        self._mode = mode
        self._pending: Flashcard | None = None
        self._total = 0
        self._correct = 0
        self._missed: list[Flashcard] = []

    def next_question(self) -> Flashcard | None:
        """Ask the mode for the next card and remember it as pending.

        Returns:
            The next card, or ``None`` when the mode has no more cards.

        Raises:
            ValueError: If the previous question was not answered yet.
        """
        if self._pending is not None:
            raise ValueError("The current question has not been answered yet.")
        self._pending = self._mode.next_card()
        return self._pending

    def submit_answer(self, answer: str) -> AnswerResult:
        """Check the answer to the pending question.

        Args:
            answer: The text typed by the user.

        Returns:
            Whether the answer was correct and the expected answer.

        Raises:
            ValueError: If there is no pending question.
        """
        card = self._pending
        if card is None:
            raise ValueError("There is no question waiting for an answer.")
        correct = is_correct_answer(answer, card.back)
        self._mode.record_result(card, correct)
        self._total += 1
        if correct:
            self._correct += 1
        elif card not in self._missed:
            # Two cards with identical text are the same term, so the term
            # appears only once.
            self._missed.append(card)
        self._pending = None
        return AnswerResult(correct=correct, expected=card.back)

    def stats(self) -> SessionStats:
        """Return the current statistics.

        A question that was asked but not answered is not counted.

        Returns:
            The statistics so far.
        """
        return SessionStats(
            total_questions=self._total,
            correct_answers=self._correct,
            missed_terms=tuple(card.front for card in self._missed),
        )
