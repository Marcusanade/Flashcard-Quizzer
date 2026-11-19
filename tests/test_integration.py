"""Integration tests: loader, quiz engine and console interface working together.

They use the two real decks in the ``data`` folder. The expected sequences were
calculated by an independent simulation of the rules and are written here as
literals, never built with functions from the code under test.
"""

import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

import ui
from data_loader import load_flashcards
from models import Flashcard
from quiz_engine import AnswerResult, QuizModeFactory, QuizSession
from tests.helpers import (
    LineRecorder,
    ParsedReport,
    green,
    parse_report,
    red,
    run_ui,
    write_deck,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

GLOSSARY = [
    ("API", "Application Programming Interface"),
    ("CDN", "Content Delivery Network"),
    ("CPU", "Central Processing Unit"),
    ("DNS", "Domain Name System"),
    ("HTTP", "Hypertext Transfer Protocol"),
    ("IP", "Internet Protocol"),
    ("RAM", "Random Access Memory"),
    ("SSH", "Secure Shell"),
    ("TLS", "Transport Layer Security"),
    ("VPN", "Virtual Private Network"),
]
PYTHON_BASICS = [
    ("Which keyword defines a function?", "def"),
    ("Which built-in function returns the length of a list?", "len"),
    ("Which keyword starts a loop over the items of a sequence?", "for"),
    ("What is the boolean type called?", "bool"),
    ("Which keyword handles an exception raised in a try block?", "except"),
    ('Which built-in function converts the string "42" to an integer?', "int"),
    ("Which mutable built-in type stores key-value pairs?", "dict"),
    ("Which keyword imports a module?", "import"),
]

# The layout of the report box is pinned in tests/test_ui.py. These tests check
# the numbers and the missed terms of real games.
ACC_ZERO = "[--------------------]   0.0%"
ACC_HALF = "[##########----------]  50.0%"
ACC_TWO_THIRDS = "[#############-------]  66.7%"
ACC_88 = "[##################--]  88.9%"
ACC_FULL = "[####################] 100.0%"
QUESTION_PATTERN = r"^Q(\d+)( \(review\))?: (.*)$"


def expected_game_lines(
    deck: Sequence[tuple[str, str]],
    positions: Sequence[int],
    correct: Sequence[bool],
) -> list[str]:
    """Build the expected question and feedback lines of a game."""
    lines: list[str] = []
    for index, (position, is_correct) in enumerate(zip(positions, correct)):
        front, back = deck[position - 1]
        is_review = position in positions[:index]
        label = f"Q{index + 1} (review)" if is_review else f"Q{index + 1}"
        lines.append(f"{label}: {front}")
        lines.append(
            green("Correct!") if is_correct else red(f"Incorrect. Answer: {back}")
        )
    return lines


def summary_values(total: str, accuracy: str, rank: str) -> dict[str, str]:
    """Build the expected values of a summary box."""
    return {"Total questions": total, "Accuracy": accuracy, "Rank": rank}


def full_values(
    mode: str,
    deck_file: str,
    size: str,
    session: str,
    total: str,
    correct: str,
    incorrect: str,
    accuracy: str,
    rank: str,
) -> dict[str, str]:
    """Build the expected values of the full report box."""
    return {
        "Mode": mode,
        "Deck file": deck_file,
        "Deck size": size,
        "Session": session,
        "Total questions": total,
        "Correct answers": correct,
        "Incorrect answers": incorrect,
        "Accuracy": accuracy,
        "Rank": rank,
    }


def assert_ends_with_report(
    output: Sequence[str],
    prefix: Sequence[str],
    values: dict[str, str],
    missed: Sequence[str],
) -> None:
    """Assert the lines before the box and the content of the box."""
    assert output[: len(prefix)] == list(prefix)
    assert parse_report(output[len(prefix) :]) == ParsedReport(values, list(missed))


class Learner:
    """Callable that replaces ``input()`` and answers by looking at the screen."""

    def __init__(
        self,
        deck: Sequence[tuple[str, str]],
        recorder: LineRecorder,
        decide: Callable[[str, int], bool],
    ) -> None:
        """Store the deck, the recorded output and the decision function."""
        self._backs = dict(deck)
        self._recorder = recorder
        self._decide = decide
        self._times_asked: dict[str, int] = {}

    def __call__(self, prompt: str) -> str:
        """Answer the last question shown, right or wrong as decided."""
        last = self._recorder.lines[-1]
        match = re.match(QUESTION_PATTERN, last)
        assert match is not None, f"The last line is not a question: {last!r}"
        front = match.group(3)
        times = self._times_asked.get(front, 0) + 1
        self._times_asked[front] = times
        return self._backs[front] if self._decide(front, times) else "x"


def play_with_learner(
    argv: Sequence[str],
    deck: Sequence[tuple[str, str]],
    decide: Callable[[str, int], bool],
) -> tuple[int, list[str], list[str]]:
    """Run the interface with a learner and return code, output and errors."""
    output = LineRecorder()
    errors = LineRecorder()
    learner = Learner(deck, output, decide)
    exit_code = ui.run(argv, learner, output, errors)
    return exit_code, output.lines, errors.lines


def question_fronts(output: Sequence[str]) -> list[str]:
    """Return the fronts of the question lines in the output."""
    matches = (re.match(QUESTION_PATTERN, line) for line in output)
    return [match.group(3) for match in matches if match is not None]


# --- Real decks --------------------------------------------------------------


def test_real_decks_have_the_expected_content() -> None:
    # This pins the real decks, so a change in them must be a conscious
    # decision.
    glossary = load_flashcards(DATA_DIR / "glossary.json")
    python_basics = load_flashcards(DATA_DIR / "python_basics.json")

    assert glossary == [Flashcard(front, back) for front, back in GLOSSARY]
    assert python_basics == [Flashcard(front, back) for front, back in PYTHON_BASICS]


# --- Full sessions -----------------------------------------------------------


def test_full_session() -> None:
    cards = load_flashcards(DATA_DIR / "glossary.json")
    session = QuizSession(QuizModeFactory.create_mode("sequential", cards))
    results: list[AnswerResult] = []

    for answer in ("Application Programming Interface", "x", "central processing unit"):
        assert session.next_question() is not None
        results.append(session.submit_answer(answer))
    stats = session.stats()
    next_card = session.next_question()
    stats_after = session.stats()

    assert results == [
        AnswerResult(correct=True, expected="Application Programming Interface"),
        AnswerResult(correct=False, expected="Content Delivery Network"),
        AnswerResult(correct=True, expected="Central Processing Unit"),
    ]
    assert stats.total_questions == 3
    assert stats.correct_answers == 2
    assert stats.accuracy_percent == pytest.approx(66.67, abs=0.01)
    assert stats.missed_terms == ("CDN",)
    assert next_card is not None
    assert next_card.front == "DNS"
    assert stats_after.total_questions == 3


def test_full_session_through_the_cli() -> None:
    argv = ["-f", str(DATA_DIR / "glossary.json")]

    result = run_ui(
        argv,
        "Application Programming Interface",
        "x",
        "central processing unit",
        "exit",
    )

    assert result.exit_code == 0
    prefix = [
        "Q1: API",
        green("Correct!"),
        "Q2: CDN",
        red("Incorrect. Answer: Content Delivery Network"),
        "Q3: CPU",
        green("Correct!"),
        "Q4: DNS",
        "Quiz stopped.",
        "",
    ]
    assert_ends_with_report(
        result.output, prefix, summary_values("3", ACC_TWO_THIRDS, "C"), ["CDN"]
    )


def test_glossary_sequential_all_correct() -> None:
    argv = ["-f", str(DATA_DIR / "glossary.json")]

    result = run_ui(argv, *[back for _, back in GLOSSARY])

    prefix = expected_game_lines(GLOSSARY, range(1, 11), [True] * 10)
    assert_ends_with_report(
        result.output,
        prefix + ["Quiz finished.", ""],
        summary_values("10", ACC_FULL, "S"),
        [],
    )


def test_glossary_sequential_all_wrong_with_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(PROJECT_ROOT)

    result = run_ui(["-f", "data/glossary.json", "--stats"], *["x"] * 10)

    prefix = expected_game_lines(GLOSSARY, range(1, 11), [False] * 10)
    values = full_values(
        "sequential",
        "data/glossary.json",
        "10",
        "finished",
        "10",
        "0",
        "10",
        ACC_ZERO,
        "D",
    )
    assert_ends_with_report(
        result.output,
        prefix + ["Quiz finished.", ""],
        values,
        [front for front, _ in GLOSSARY],
    )


def test_python_basics_object_format_sequential_all_correct() -> None:
    argv = ["-f", str(DATA_DIR / "python_basics.json")]

    result = run_ui(argv, *[back for _, back in PYTHON_BASICS])

    prefix = expected_game_lines(PYTHON_BASICS, range(1, 9), [True] * 8)
    assert_ends_with_report(
        result.output,
        prefix + ["Quiz finished.", ""],
        summary_values("8", ACC_FULL, "S"),
        [],
    )


# --- Adaptive mode with the real decks ---------------------------------------


def test_python_basics_adaptive_all_wrong_retires_every_card_after_three_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(PROJECT_ROOT)
    positions = [1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 5, 6, 4, 5, 6, 4, 5, 6, 7, 8, 7, 8, 7, 8]

    code, output, errors = play_with_learner(
        ["-m", "adaptive", "-f", "data/python_basics.json", "--stats"],
        PYTHON_BASICS,
        lambda front, times: False,
    )

    assert code == 0
    assert errors == []
    # The long fronts are wrapped in the box, and the reader joins them.
    prefix = expected_game_lines(PYTHON_BASICS, positions, [False] * 24)
    values = full_values(
        "adaptive",
        "data/python_basics.json",
        "8",
        "finished",
        "24",
        "0",
        "24",
        ACC_ZERO,
        "D",
    )
    assert_ends_with_report(
        output,
        prefix + ["Quiz finished.", ""],
        values,
        [front for front, _ in PYTHON_BASICS],
    )


def test_python_basics_adaptive_game_played_by_hand() -> None:
    # The review of the failed card appears two questions later, as the
    # default rest for 8 cards is 2.
    argv = ["-m", "adaptive", "-f", str(DATA_DIR / "python_basics.json")]
    positions = [1, 2, 3, 4, 5, 6, 7, 5, 8]
    correct = [True, True, True, True, False, True, True, True, True]

    result = run_ui(
        argv, "def", "len", "for", "bool", "raise", "int", "dict", "except", "import"
    )

    prefix = expected_game_lines(PYTHON_BASICS, positions, correct)
    assert_ends_with_report(
        result.output,
        prefix + ["Quiz finished.", ""],
        summary_values("9", ACC_88, "B"),
        ["Which keyword handles an exception raised in a try block?"],
    )


def test_glossary_adaptive_each_card_fails_once_then_is_answered_correctly() -> None:
    # Card 10 is repeated in a row only because it is the only card left.
    positions = [1, 2, 3, 1, 2, 3, 4, 5, 6, 4, 5, 6, 7, 8, 9, 7, 8, 9, 10, 10]
    correct = [positions[:i].count(p) > 0 for i, p in enumerate(positions)]

    code, output, errors = play_with_learner(
        ["-m", "adaptive", "-f", str(DATA_DIR / "glossary.json")],
        GLOSSARY,
        lambda front, times: times >= 2,
    )

    assert code == 0
    assert errors == []
    assert_ends_with_report(
        output,
        expected_game_lines(GLOSSARY, positions, correct) + ["Quiz finished.", ""],
        summary_values("20", ACC_HALF, "D"),
        [front for front, _ in GLOSSARY],
    )


def test_glossary_adaptive_always_wrong() -> None:
    positions = [1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 5, 6, 4, 5, 6, 4, 5, 6]
    positions += [7, 8, 9, 7, 8, 9, 7, 8, 9, 10, 10, 10]

    code, output, errors = play_with_learner(
        ["-m", "adaptive", "-f", str(DATA_DIR / "glossary.json")],
        GLOSSARY,
        lambda front, times: False,
    )

    assert code == 0
    assert errors == []
    assert_ends_with_report(
        output,
        expected_game_lines(GLOSSARY, positions, [False] * 30) + ["Quiz finished.", ""],
        summary_values("30", ACC_ZERO, "D"),
        [front for front, _ in GLOSSARY],
    )


# --- Random mode -------------------------------------------------------------


def test_glossary_random_mode_asks_every_card_once() -> None:
    code, output, errors = play_with_learner(
        ["-m", "random", "-f", str(DATA_DIR / "glossary.json")],
        GLOSSARY,
        lambda front, times: True,
    )

    assert code == 0
    assert errors == []
    assert sorted(question_fronts(output)) == sorted(front for front, _ in GLOSSARY)
    assert not any("(review)" in line for line in output)
    assert output[1:20:2] == [green("Correct!")] * 10
    assert output[20:22] == ["Quiz finished.", ""]
    assert parse_report(output[22:]) == ParsedReport(
        summary_values("10", ACC_FULL, "S"), []
    )


def test_random_mode_through_the_cli_does_not_always_follow_file_order() -> None:
    # The chance of 5 identical orders in a row is below 1 in 10^30.
    file_order = [front for front, _ in GLOSSARY]
    orders: list[list[str]] = []

    for _ in range(5):
        _, output, _ = play_with_learner(
            ["-m", "random", "-f", str(DATA_DIR / "glossary.json")],
            GLOSSARY,
            lambda front, times: False,
        )
        orders.append(question_fronts(output))

    assert any(order != file_order for order in orders)


# --- Edge cases --------------------------------------------------------------


@pytest.mark.parametrize("mode", ["sequential", "random", "adaptive"])
def test_one_card_deck_answered_correctly_in_every_mode(
    tmp_path: Path, mode: str
) -> None:
    path = write_deck(tmp_path, [("A", "a")])

    result = run_ui(["-m", mode, "-f", str(path)], "a")

    prefix = ["Q1: A", green("Correct!"), "Quiz finished.", ""]
    assert_ends_with_report(
        result.output, prefix, summary_values("1", ACC_FULL, "S"), []
    )


def test_one_card_deck_adaptive_wrong_three_times(tmp_path: Path) -> None:
    path = write_deck(tmp_path, [("A", "a")])

    result = run_ui(["-m", "adaptive", "-f", str(path)], "x", "x", "x")

    prefix = [
        "Q1: A",
        red("Incorrect. Answer: a"),
        "Q2 (review): A",
        red("Incorrect. Answer: a"),
        "Q3 (review): A",
        red("Incorrect. Answer: a"),
        "Quiz finished.",
        "",
    ]
    assert_ends_with_report(
        result.output, prefix, summary_values("3", ACC_ZERO, "D"), ["A"]
    )


def test_real_deck_answers_ignore_spaces_and_case() -> None:
    argv = ["-f", str(DATA_DIR / "glossary.json")]

    result = run_ui(argv, "  APPLICATION programming INTERFACE  ", "exit")

    prefix = ["Q1: API", green("Correct!"), "Q2: CDN", "Quiz stopped.", ""]
    assert_ends_with_report(
        result.output, prefix, summary_values("1", ACC_FULL, "S"), []
    )


def test_non_ascii_deck_is_read_as_utf8_and_compared_with_casefold(
    tmp_path: Path,
) -> None:
    # The file is read as UTF-8, and the second reply needs casefold and not
    # lower: "STRASSE" only matches "straße" with casefold.
    path = write_deck(tmp_path, [("ñ", "é"), ("Über", "straße")])

    result = run_ui(["-f", str(path)], "É", "STRASSE")

    prefix = [
        "Q1: ñ",
        green("Correct!"),
        "Q2: Über",
        green("Correct!"),
        "Quiz finished.",
        "",
    ]
    assert_ends_with_report(
        result.output, prefix, summary_values("2", ACC_FULL, "S"), []
    )


# --- Separate process --------------------------------------------------------


def test_main_script_in_a_separate_process() -> None:
    # The prompt "> " is written without a line break, so the feedback lines
    # are glued to it in the captured text. This test does not count for the
    # coverage because it runs in another process.
    replies = "\n".join(back for _, back in GLOSSARY) + "\n"

    completed = subprocess.run(
        [sys.executable, "main.py", "-f", "data/glossary.json"],
        input=replies,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=PROJECT_ROOT,
        timeout=30,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    lines = completed.stdout.splitlines()
    finished = lines.index("Quiz finished.")
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert "Quiz finished." in completed.stdout
    assert completed.stdout.count(green("Correct!")) == 10
    assert lines[finished + 1] == ""
    assert parse_report(lines[finished + 2 :]) == ParsedReport(
        summary_values("10", ACC_FULL, "S"), []
    )
    assert lines[0] == green("+" + "=" * 58 + "+")
    assert "READY PLAYER 1   MODE: SEQUENTIAL   CARDS: 10" in completed.stdout
