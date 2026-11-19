"""Tests for the ``--limit`` option: the end of the session after N answers.

The limit is a rule of the session, not of the quiz modes. The engine tests use
``QuizSession`` directly, then the parser and ``ui.run`` are tested. The
expected results of the ``run`` tests were calculated by an independent
simulation of the rules and are written here as literals.
"""

import re
from pathlib import Path

import pytest

from models import Flashcard
from quiz_engine import AdaptiveMode, QuizMode, QuizSession
from tests.helpers import (
    ParsedReport,
    green,
    make_cards,
    make_pairs,
    parse_report,
    red,
    run_ui,
    write_deck,
)
from ui import build_parser

ACC_FULL = "[####################] 100.0%"
ACC_TWO_THIRDS = "[#############-------]  66.7%"
ACC_ZERO = "[--------------------]   0.0%"


class CountingMode(QuizMode):
    """Mode used only by these tests: cards in order, counting the calls.

    Attributes:
        calls: How many times ``next_card`` was called, including the calls
            that returned ``None``.
    """

    def __init__(self, cards: list[Flashcard]) -> None:
        """Store the cards and start counting."""
        super().__init__(cards)
        self.calls = 0
        self._index = 0

    def next_card(self) -> Flashcard | None:
        """Return the next card in order, or ``None`` at the end."""
        self.calls += 1
        if self._index >= len(self._cards):
            return None
        card = self._cards[self._index]
        self._index += 1
        return card


def answer(session: QuizSession, text: str) -> None:
    """Ask the next question and submit the given answer."""
    assert session.next_question() is not None
    session.submit_answer(text)


def box_start(output: list[str]) -> int:
    """Return the position of the first line of the report box."""
    return next(i for i, line in enumerate(output) if line.startswith("+="))


def summary(total: str, accuracy: str, rank: str) -> dict[str, str]:
    """Build the expected values of a summary box."""
    return {"Total questions": total, "Accuracy": accuracy, "Rank": rank}


def assert_game(
    output: list[str],
    prefix: list[str],
    values: dict[str, str],
    missed: list[str],
) -> None:
    """Assert the lines before the box and the content of the box."""
    assert output[: len(prefix)] == prefix
    assert parse_report(output[len(prefix) :]) == ParsedReport(values, missed)


# --- Engine: QuizSession -----------------------------------------------------


def test_session_returns_none_after_the_limit_without_asking_the_mode() -> None:
    mode = CountingMode(make_cards("A", "B", "C", "D", "E"))
    session = QuizSession(mode, max_questions=3)

    for text in ("a", "b", "c"):
        answer(session, text)

    assert session.next_question() is None
    assert mode.calls == 3
    assert session.stats().total_questions == 3


def test_session_keeps_returning_none_and_does_not_consume_cards() -> None:
    mode = CountingMode(make_cards("A", "B", "C", "D", "E"))
    session = QuizSession(mode, max_questions=3)
    for text in ("a", "b", "c"):
        answer(session, text)

    results = [session.next_question(), session.next_question()]

    assert results == [None, None]
    assert mode.calls == 3


def test_session_without_limit_asks_every_card() -> None:
    mode = CountingMode(make_cards("A", "B", "C", "D", "E"))
    session = QuizSession(mode, max_questions=None)

    for text in ("a", "b", "c", "d", "e"):
        answer(session, text)

    assert session.next_question() is None
    assert mode.calls == 6
    assert session.stats().total_questions == 5


def test_session_limit_larger_than_the_deck_ends_with_the_cards() -> None:
    session = QuizSession(CountingMode(make_cards("A", "B")), max_questions=5)

    answer(session, "a")
    answer(session, "b")

    assert session.next_question() is None
    assert session.stats().total_questions == 2


def test_session_limit_of_one_asks_a_single_question() -> None:
    session = QuizSession(CountingMode(make_cards("A", "B")), max_questions=1)

    answer(session, "a")

    assert session.next_question() is None
    assert session.stats().total_questions == 1


def test_session_unanswered_question_does_not_count() -> None:
    session = QuizSession(CountingMode(make_cards("A", "B", "C")), max_questions=2)
    answer(session, "a")
    assert session.next_question() is not None

    with pytest.raises(ValueError, match="not been answered"):
        session.next_question()
    total_while_pending = session.stats().total_questions
    session.submit_answer("b")

    assert total_while_pending == 1
    assert session.next_question() is None


def test_session_submit_answer_after_the_limit_has_no_question_waiting() -> None:
    session = QuizSession(CountingMode(make_cards("A", "B")), max_questions=1)
    answer(session, "a")
    session.next_question()

    with pytest.raises(ValueError, match="no question waiting"):
        session.submit_answer("b")


@pytest.mark.parametrize("limit", [0, -1], ids=["zero", "negative"])
def test_session_rejects_a_limit_below_one(limit: int) -> None:
    mode = CountingMode(make_cards("A"))

    with pytest.raises(ValueError, match="max_questions must be at least 1"):
        QuizSession(mode, max_questions=limit)


def test_session_adaptive_mode_counts_repetitions() -> None:
    session = QuizSession(AdaptiveMode(make_cards("A", "B", "C")), max_questions=5)
    fronts: list[str] = []

    while (card := session.next_question()) is not None:
        fronts.append(card.front)
        session.submit_answer("x")

    stats = session.stats()
    assert fronts == ["A", "B", "C", "A", "B"]
    assert stats.total_questions == 5
    assert stats.correct_answers == 0
    assert stats.missed_terms == ("A", "B", "C")


# --- Parser ------------------------------------------------------------------


def test_parser_limit_defaults_to_none() -> None:
    args = build_parser().parse_args(["-f", "deck.json"])

    assert args.limit is None


@pytest.mark.parametrize("value", [5, 1])
def test_parser_limit_is_converted_to_an_integer(value: int) -> None:
    args = build_parser().parse_args(["-f", "deck.json", "--limit", str(value)])

    assert args.limit == value


@pytest.mark.parametrize(
    "value",
    ["0", "-3", "abc", "2.5", ""],
    ids=["zero", "negative", "letters", "decimal", "empty"],
)
def test_parser_invalid_limit_exits_with_code_2(
    value: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as info:
        build_parser().parse_args(["-f", "deck.json", "--limit", value])

    assert info.value.code == 2
    assert "positive integer" in capsys.readouterr().err


def test_parser_limit_without_value_exits_with_code_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as info:
        build_parser().parse_args(["-f", "deck.json", "--limit"])

    assert info.value.code == 2
    assert "expected one argument" in capsys.readouterr().err


def test_parser_help_lists_the_limit_option(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--help"])

    assert "--limit" in capsys.readouterr().out


# --- run ---------------------------------------------------------------------


def test_run_limit_stops_a_sequential_quiz_as_a_normal_end(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B", "C", "D", "E"))

    result = run_ui(["-f", str(path), "--limit", "3"], "a", "b", "c")

    assert result.exit_code == 0
    prefix = [
        "Q1: A",
        green("Correct!"),
        "Q2: B",
        green("Correct!"),
        "Q3: C",
        green("Correct!"),
        "Quiz finished.",
        "",
    ]
    assert_game(result.output, prefix, summary("3", ACC_FULL, "S"), [])


def test_run_limit_counts_wrong_answers_too(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B", "C", "D", "E"))

    result = run_ui(["-f", str(path), "--limit", "3"], "a", "x", "c")

    prefix = [
        "Q1: A",
        green("Correct!"),
        "Q2: B",
        red("Incorrect. Answer: b"),
        "Q3: C",
        green("Correct!"),
        "Quiz finished.",
        "",
    ]
    assert_game(result.output, prefix, summary("3", ACC_TWO_THIRDS, "C"), ["B"])


def test_run_limit_larger_than_the_deck_ends_with_the_cards(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B"))

    result = run_ui(["-f", str(path), "--limit", "5"], "a", "b")

    prefix = [
        "Q1: A",
        green("Correct!"),
        "Q2: B",
        green("Correct!"),
        "Quiz finished.",
        "",
    ]
    assert_game(result.output, prefix, summary("2", ACC_FULL, "S"), [])


def test_run_limit_in_adaptive_mode_counts_the_reviews(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B", "C"))

    result = run_ui(["-m", "adaptive", "-f", str(path), "--limit", "5"], *["x"] * 5)

    prefix = [
        "Q1: A",
        red("Incorrect. Answer: a"),
        "Q2: B",
        red("Incorrect. Answer: b"),
        "Q3: C",
        red("Incorrect. Answer: c"),
        "Q4 (review): A",
        red("Incorrect. Answer: a"),
        "Q5 (review): B",
        red("Incorrect. Answer: b"),
        "Quiz finished.",
        "",
    ]
    assert_game(result.output, prefix, summary("5", ACC_ZERO, "D"), ["A", "B", "C"])


def test_run_limit_in_random_mode_asks_that_many_distinct_cards(
    tmp_path: Path,
) -> None:
    fronts = [f"F{number:02d}" for number in range(1, 11)]
    path = write_deck(tmp_path, make_pairs(*fronts))

    result = run_ui(["-m", "random", "-f", str(path), "--limit", "4"], *["x"] * 4)

    output = result.output
    start = box_start(output)
    matches = [re.match(r"^Q\d+: (F\d\d)$", line) for line in output]
    asked = [match.group(1) for match in matches if match is not None]
    assert len(asked) == 4
    assert len(set(asked)) == 4
    assert set(asked) <= set(fronts)
    assert output[start - 1] == ""
    assert output[start - 2] == "Quiz finished."
    assert parse_report(output[start:]) == ParsedReport(
        summary("4", ACC_ZERO, "D"), asked
    )


def test_run_limit_reached_is_a_finished_session_in_the_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_deck(tmp_path, make_pairs("A", "B", "C", "D", "E"))
    monkeypatch.chdir(tmp_path)

    result = run_ui(["-f", "deck.json", "--limit", "2", "--stats"], "a", "b")

    values = {
        "Mode": "sequential",
        "Deck file": "deck.json",
        "Deck size": "5",
        "Session": "finished",
        "Total questions": "2",
        "Correct answers": "2",
        "Incorrect answers": "0",
        "Accuracy": ACC_FULL,
        "Rank": "S",
    }
    prefix = [
        "Q1: A",
        green("Correct!"),
        "Q2: B",
        green("Correct!"),
        "Quiz finished.",
        "",
    ]
    assert_game(result.output, prefix, values, [])


def test_run_quitting_before_the_limit_is_a_stopped_quiz(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B", "C", "D", "E"))

    result = run_ui(["-f", str(path), "--limit", "3"], "a", "exit")

    prefix = ["Q1: A", green("Correct!"), "Q2: B", "Quiz stopped.", ""]
    assert_game(result.output, prefix, summary("1", ACC_FULL, "S"), [])


def test_run_invalid_limit_exits_with_code_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_deck(tmp_path, make_pairs("A"))

    with pytest.raises(SystemExit) as info:
        run_ui(["-f", str(path), "--limit", "0"])

    assert info.value.code == 2
    assert "positive integer" in capsys.readouterr().err
