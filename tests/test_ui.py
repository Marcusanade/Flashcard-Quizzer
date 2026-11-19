"""Unit tests for the console interface (``ui.py``) and for ``main.py``.

The expected report boxes are written by hand as literal lists, never built
with functions from ``ui``, so a change in the layout is detected.
"""

import io
import runpy
from pathlib import Path

import pytest

import ui
from models import Flashcard
from quiz_engine import (
    AnswerResult,
    QuizMode,
    QuizSession,
    SequentialMode,
    SessionStats,
)
from tests.helpers import (
    LineRecorder,
    ScriptedInput,
    green,
    make_cards,
    make_pairs,
    red,
    run_ui,
    write_deck,
)
from ui import (
    ReadResult,
    _accuracy_bar,
    _accuracy_text,
    _ask_questions,
    _border,
    _feedback_line,
    _fit,
    _missed_rows,
    _pair_row,
    _question_label,
    _question_line,
    _rank,
    _read_answer,
    _report_lines,
    _row,
    _summary_lines,
    _title_row,
    build_parser,
)

HEAD = [
    "+==========================================================+",
    "|                      SESSION REPORT                      |",
    "+==========================================================+",
]
DASH = "+----------------------------------------------------------+"
END = "+==========================================================+"

SUMMARY_3_2_B = (
    HEAD
    + [
        "| Total questions    3                                     |",
        "| Accuracy           [#############-------]  66.7%         |",
        "| Rank               C                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms                                             |",
        "|   - B                                                    |",
    ]
    + [END]
)
SUMMARY_7_4_B = (
    HEAD
    + [
        "| Total questions    7                                     |",
        "| Accuracy           [###########---------]  57.1%         |",
        "| Rank               D                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms                                             |",
        "|   - B                                                    |",
    ]
    + [END]
)
SUMMARY_1_0_A = (
    HEAD
    + [
        "| Total questions    1                                     |",
        "| Accuracy           [--------------------]   0.0%         |",
        "| Rank               D                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms                                             |",
        "|   - A                                                    |",
    ]
    + [END]
)
SUMMARY_0_0 = (
    HEAD
    + [
        "| Total questions    0                                     |",
        "| Accuracy           [--------------------]   0.0%         |",
        "| Rank               -                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms: none                                       |",
    ]
    + [END]
)
SUMMARY_3_3 = (
    HEAD
    + [
        "| Total questions    3                                     |",
        "| Accuracy           [####################] 100.0%         |",
        "| Rank               S                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms: none                                       |",
    ]
    + [END]
)
SUMMARY_1_1 = (
    HEAD
    + [
        "| Total questions    1                                     |",
        "| Accuracy           [####################] 100.0%         |",
        "| Rank               S                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms: none                                       |",
    ]
    + [END]
)
SUMMARY_2_2 = (
    HEAD
    + [
        "| Total questions    2                                     |",
        "| Accuracy           [####################] 100.0%         |",
        "| Rank               S                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms: none                                       |",
    ]
    + [END]
)
SUMMARY_2_1_B = (
    HEAD
    + [
        "| Total questions    2                                     |",
        "| Accuracy           [##########----------]  50.0%         |",
        "| Rank               D                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms                                             |",
        "|   - B                                                    |",
    ]
    + [END]
)
SUMMARY_9_8_EXCEPT = (
    HEAD
    + [
        "| Total questions    9                                     |",
        "| Accuracy           [##################--]  88.9%         |",
        "| Rank               B                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms                                             |",
        "|   - Which keyword handles an exception raised in a try   |",
        "|     block?                                               |",
    ]
    + [END]
)
SUMMARY_LONG_WORD = (
    HEAD
    + [
        "| Total questions    1                                     |",
        "| Accuracy           [--------------------]   0.0%         |",
        "| Rank               D                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms                                             |",
        "|   - XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX |",
        "|     XXXXXXXXXXXXXXXXXX                                   |",
    ]
    + [END]
)

REPORT_SEQ_3_2_B = (
    HEAD
    + [
        "| Mode               sequential                            |",
        "| Deck file          deck.json                             |",
        "| Deck size          3                                     |",
        "| Session            finished                              |",
    ]
    + [DASH]
    + [
        "| Total questions    3                                     |",
        "| Correct answers    2                                     |",
        "| Incorrect answers  1                                     |",
        "| Accuracy           [#############-------]  66.7%         |",
        "| Rank               C                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms                                             |",
        "|   - B                                                    |",
    ]
    + [END]
)
REPORT_SEQ_0_3_ABC = (
    HEAD
    + [
        "| Mode               sequential                            |",
        "| Deck file          deck.json                             |",
        "| Deck size          3                                     |",
        "| Session            finished                              |",
    ]
    + [DASH]
    + [
        "| Total questions    3                                     |",
        "| Correct answers    0                                     |",
        "| Incorrect answers  3                                     |",
        "| Accuracy           [--------------------]   0.0%         |",
        "| Rank               D                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms                                             |",
        "|   - A                                                    |",
        "|   - B                                                    |",
        "|   - C                                                    |",
    ]
    + [END]
)
REPORT_ADAPTIVE_7_4_B = (
    HEAD
    + [
        "| Mode               adaptive                              |",
        "| Deck file          deck.json                             |",
        "| Deck size          5                                     |",
        "| Session            finished                              |",
    ]
    + [DASH]
    + [
        "| Total questions    7                                     |",
        "| Correct answers    4                                     |",
        "| Incorrect answers  3                                     |",
        "| Accuracy           [###########---------]  57.1%         |",
        "| Rank               D                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms                                             |",
        "|   - B                                                    |",
    ]
    + [END]
)
REPORT_ADAPTIVE_STOPPED_1_1 = (
    HEAD
    + [
        "| Mode               adaptive                              |",
        "| Deck file          deck.json                             |",
        "| Deck size          5                                     |",
        "| Session            stopped                               |",
    ]
    + [DASH]
    + [
        "| Total questions    1                                     |",
        "| Correct answers    1                                     |",
        "| Incorrect answers  0                                     |",
        "| Accuracy           [####################] 100.0%         |",
        "| Rank               S                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms: none                                       |",
    ]
    + [END]
)
REPORT_RANDOM_STOPPED_0 = (
    HEAD
    + [
        "| Mode               random                                |",
        "| Deck file          deck.json                             |",
        "| Deck size          3                                     |",
        "| Session            stopped                               |",
    ]
    + [DASH]
    + [
        "| Total questions    0                                     |",
        "| Correct answers    0                                     |",
        "| Incorrect answers  0                                     |",
        "| Accuracy           [--------------------]   0.0%         |",
        "| Rank               -                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms: none                                       |",
    ]
    + [END]
)
REPORT_LONG_PATH = (
    HEAD
    + [
        "| Mode               adaptive                              |",
        "| Deck file          ...ython_basics_extended_edition.json |",
        "| Deck size          8                                     |",
        "| Session            finished                              |",
    ]
    + [DASH]
    + [
        "| Total questions    9                                     |",
        "| Correct answers    8                                     |",
        "| Incorrect answers  1                                     |",
        "| Accuracy           [##################--]  88.9%         |",
        "| Rank               B                                     |",
    ]
    + [DASH]
    + [
        "| Missed terms: none                                       |",
    ]
    + [END]
)
ALL_BLOCKS = [
    HEAD,
    SUMMARY_3_2_B,
    SUMMARY_7_4_B,
    SUMMARY_1_0_A,
    SUMMARY_0_0,
    SUMMARY_3_3,
    SUMMARY_1_1,
    SUMMARY_2_2,
    SUMMARY_2_1_B,
    SUMMARY_9_8_EXCEPT,
    SUMMARY_LONG_WORD,
    REPORT_SEQ_3_2_B,
    REPORT_SEQ_0_3_ABC,
    REPORT_ADAPTIVE_7_4_B,
    REPORT_ADAPTIVE_STOPPED_1_1,
    REPORT_RANDOM_STOPPED_0,
    REPORT_LONG_PATH,
]
ALL_BLOCK_IDS = [
    "head",
    "summary-3-2-b",
    "summary-7-4-b",
    "summary-1-0-a",
    "summary-0-0",
    "summary-3-3",
    "summary-1-1",
    "summary-2-2",
    "summary-2-1-b",
    "summary-9-8-except",
    "summary-long-word",
    "report-seq-3-2-b",
    "report-seq-0-3-abc",
    "report-adaptive-7-4-b",
    "report-adaptive-stopped-1-1",
    "report-random-stopped-0",
    "report-long-path",
]
LONG_DECK_PATH = (
    "C:/Users/someone/Documents/My Decks/python_basics_extended_edition.json"
)
EXCEPT_TERM = "Which keyword handles an exception raised in a try block?"

ABC_FEEDBACK_AB = ["Q1: A", green("Correct!"), "Q2: B"]
ABC_AXC_LINES = [
    "Q1: A",
    green("Correct!"),
    "Q2: B",
    red("Incorrect. Answer: b"),
    "Q3: C",
    green("Correct!"),
    "Quiz finished.",
    "",
]
ADAPTIVE_LINES = [
    "Q1: A",
    green("Correct!"),
    "Q2: B",
    red("Incorrect. Answer: b"),
    "Q3: C",
    green("Correct!"),
    "Q4: D",
    green("Correct!"),
    "Q5 (review): B",
    red("Incorrect. Answer: b"),
    "Q6: E",
    green("Correct!"),
    "Q7 (review): B",
    red("Incorrect. Answer: b"),
    "Quiz finished.",
    "",
]
ADAPTIVE_REPLIES = ["a", "wrong", "c", "d", "wrong", "e", "wrong"]


def use_deck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pairs: list[tuple[str, str]],
    as_object: bool = False,
) -> None:
    """Write ``deck.json`` in ``tmp_path`` and make it the current directory."""
    write_deck(tmp_path, pairs, as_object=as_object)
    monkeypatch.chdir(tmp_path)


# --- build_parser ------------------------------------------------------------


def test_build_parser_defaults() -> None:
    args = build_parser().parse_args(["-f", "deck.json"])

    assert args.mode == "sequential"
    assert args.stats is False


@pytest.mark.parametrize(
    ("typed", "expected"),
    [("Adaptive", "adaptive"), ("RANDOM", "random")],
    ids=["adaptive-mixed-case", "random-uppercase"],
)
def test_build_parser_mode_is_case_insensitive(typed: str, expected: str) -> None:
    args = build_parser().parse_args(["-f", "deck.json", "-m", typed])

    assert args.mode == expected


def test_build_parser_stats_flag_is_true() -> None:
    args = build_parser().parse_args(["-f", "deck.json", "--stats"])

    assert args.stats is True


def test_build_parser_long_options_keep_the_file_text() -> None:
    args = build_parser().parse_args(["--file", "My Decks/a.json", "--mode", "random"])

    assert args.file == "My Decks/a.json"
    assert args.mode == "random"


def test_build_parser_invalid_mode_exits_with_code_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as info:
        build_parser().parse_args(["-f", "deck.json", "-m", "foo"])

    assert info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_build_parser_missing_file_exits_with_code_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as info:
        build_parser().parse_args([])

    assert info.value.code == 2
    assert "required" in capsys.readouterr().err


def test_build_parser_help_exits_with_code_0_and_lists_options(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as info:
        build_parser().parse_args(["--help"])

    help_text = capsys.readouterr().out
    assert info.value.code == 0
    for expected in ("-f", "--mode", "--stats", "adaptive", "random", "sequential"):
        assert expected in help_text


def test_build_parser_prog_is_main_py() -> None:
    assert build_parser().prog == "main.py"


# --- Small text functions ----------------------------------------------------


@pytest.mark.parametrize(
    ("number", "is_review", "expected"),
    [(1, False, "Q1"), (5, True, "Q5 (review)")],
    ids=["first", "review"],
)
def test_question_label(number: int, is_review: bool, expected: str) -> None:
    assert _question_label(number, is_review) == expected


def test_question_line_joins_label_and_front() -> None:
    line = _question_line(2, Flashcard("What?", "x"), True)

    assert line == "Q2 (review): What?"


def test_feedback_line_correct_is_green() -> None:
    result = AnswerResult(correct=True, expected="b")

    assert _feedback_line(result) == green("Correct!")


def test_feedback_line_incorrect_is_red_with_expected_answer() -> None:
    result = AnswerResult(correct=False, expected="b")

    assert _feedback_line(result) == red("Incorrect. Answer: b")


@pytest.mark.parametrize(
    ("total", "correct", "expected"),
    [
        (3, 1, "33.3%"),
        (3, 2, "66.7%"),
        (7, 4, "57.1%"),
        (0, 0, "0.0%"),
        (4, 4, "100.0%"),
    ],
    ids=["one-of-three", "two-of-three", "four-of-seven", "none", "all"],
)
def test_accuracy_text(total: int, correct: int, expected: str) -> None:
    stats = SessionStats(
        total_questions=total, correct_answers=correct, missed_terms=()
    )

    assert _accuracy_text(stats) == expected


# --- _summary_lines and _report_lines ----------------------------------------


def test_summary_lines_with_a_missed_term() -> None:
    lines = _summary_lines(SessionStats(3, 2, ("B",)))

    assert lines == SUMMARY_3_2_B


def test_summary_lines_without_questions() -> None:
    lines = _summary_lines(SessionStats(0, 0, ()))

    assert lines == SUMMARY_0_0


def test_report_lines_sequential_session() -> None:
    lines = _report_lines(
        SessionStats(3, 2, ("B",)), "sequential", "deck.json", 3, True
    )

    assert lines == REPORT_SEQ_3_2_B


def test_report_lines_incorrect_answers_differ_from_distinct_cards_missed() -> None:
    # This case (7 questions, 4 correct answers) is important because the
    # incorrect answers (3) and the number of missed cards (1) are
    # different numbers.
    lines = _report_lines(SessionStats(7, 4, ("B",)), "adaptive", "deck.json", 5, True)

    assert lines == REPORT_ADAPTIVE_7_4_B


def test_report_lines_stopped_session() -> None:
    lines = _report_lines(SessionStats(0, 0, ()), "random", "deck.json", 3, False)

    assert lines == REPORT_RANDOM_STOPPED_0


# --- Report building blocks --------------------------------------------------


@pytest.mark.parametrize("block", ALL_BLOCKS, ids=ALL_BLOCK_IDS)
def test_expected_blocks_are_60_characters_wide(block: list[str]) -> None:
    assert {len(line) for line in block} == {60}


def test_border_with_equals_and_with_dash() -> None:
    assert _border("=") == END
    assert _border("-") == DASH


def test_row_pads_the_text_to_the_box_width() -> None:
    row = _row("hi")

    assert row == "| hi" + " " * 55 + "|"
    assert row == "| hi                                                       |"


def test_title_row_centers_the_title() -> None:
    assert _title_row("SESSION REPORT") == HEAD[1]


def test_pair_row_puts_the_value_after_the_label_column() -> None:
    row = _pair_row("Mode", "adaptive")

    assert row == "| Mode               adaptive                              |"


def test_fit_short_text_is_unchanged() -> None:
    assert _fit("short", 37) == "short"


def test_fit_text_with_exactly_the_width_is_unchanged() -> None:
    assert _fit("x" * 37, 37) == "x" * 37


def test_fit_long_text_keeps_the_end() -> None:
    fitted = _fit("0123456789" * 4, 37)

    assert fitted == "...6789012345678901234567890123456789"
    assert len(fitted) == 37


def test_fit_small_width() -> None:
    assert _fit("abcdef", 4) == "...f"


@pytest.mark.parametrize(
    ("correct", "total", "filled"),
    [
        (0, 0, 0),
        (3, 3, 20),
        (8, 9, 18),
        (2, 3, 13),
        (4, 7, 11),
        (0, 1, 0),
        (1, 2, 10),
        (1, 40, 1),
        (1, 80, 0),
        (3, 80, 1),
    ],
)
def test_accuracy_bar_filled_cells(correct: int, total: int, filled: int) -> None:
    # (1, 40) is exactly half a cell and rounds up, (1, 80) is a quarter.
    bar = _accuracy_bar(correct, total)

    assert bar == "[" + "#" * filled + "-" * (20 - filled) + "]"


@pytest.mark.parametrize(
    ("correct", "total", "expected"),
    [
        (0, 0, "-"),
        (10, 10, "S"),
        (9, 10, "A"),
        (89, 100, "B"),
        (8, 10, "B"),
        (3, 4, "B"),
        (74, 100, "C"),
        (7, 10, "C"),
        (3, 5, "C"),
        (59, 100, "D"),
        (5, 10, "D"),
        (0, 10, "D"),
        (1, 3, "D"),
    ],
)
def test_rank(correct: int, total: int, expected: str) -> None:
    assert _rank(correct, total) == expected


def test_missed_rows_without_terms() -> None:
    assert _missed_rows([]) == [
        "| Missed terms: none                                       |"
    ]


def test_missed_rows_with_several_terms() -> None:
    assert _missed_rows(["C", "A"]) == [
        "| Missed terms                                             |",
        "|   - C                                                    |",
        "|   - A                                                    |",
    ]


def test_summary_lines_with_one_missed_term() -> None:
    assert _summary_lines(SessionStats(3, 2, ("B",))) == SUMMARY_3_2_B


def test_summary_lines_with_no_questions() -> None:
    assert _summary_lines(SessionStats(0, 0, ())) == SUMMARY_0_0


def test_summary_lines_with_all_answers_correct() -> None:
    assert _summary_lines(SessionStats(3, 3, ())) == SUMMARY_3_3


def test_summary_lines_wraps_a_long_term() -> None:
    lines = _summary_lines(SessionStats(9, 8, (EXCEPT_TERM,)))

    assert lines == SUMMARY_9_8_EXCEPT


def test_summary_lines_splits_a_long_word() -> None:
    lines = _summary_lines(SessionStats(1, 0, ("X" * 70,)))

    assert lines == SUMMARY_LONG_WORD


def test_report_lines_truncates_a_long_deck_path() -> None:
    stats = SessionStats(9, 8, ())

    lines = _report_lines(stats, "adaptive", LONG_DECK_PATH, 8, True)

    assert lines == REPORT_LONG_PATH


# --- _read_answer ------------------------------------------------------------


def test_read_answer_normal_answer_and_prompt() -> None:
    scripted = ScriptedInput("def")

    result = _read_answer(scripted)

    assert result == ReadResult(answer="def", interrupted=False)
    assert scripted.prompts == ["> "]


@pytest.mark.parametrize("text", ["exit", " EXIT ", "Exit"])
def test_read_answer_exit_word_means_quit(text: str) -> None:
    result = _read_answer(ScriptedInput(text))

    assert result == ReadResult(answer=None, interrupted=False)


@pytest.mark.parametrize("text", ["exit now", "exiting"])
def test_read_answer_text_that_only_contains_exit_is_normal(text: str) -> None:
    result = _read_answer(ScriptedInput(text))

    assert result == ReadResult(answer=text, interrupted=False)


def test_read_answer_empty_answer_is_a_normal_answer() -> None:
    result = _read_answer(ScriptedInput(""))

    assert result == ReadResult(answer="", interrupted=False)


@pytest.mark.parametrize(
    "exception", [KeyboardInterrupt, EOFError], ids=["ctrl-c", "end-of-input"]
)
def test_read_answer_interruption_means_quit(exception: type[BaseException]) -> None:
    result = _read_answer(ScriptedInput(exception))

    assert result == ReadResult(answer=None, interrupted=True)


# --- _ask_questions ----------------------------------------------------------


def make_session() -> QuizSession:
    """Build a sequential session over the cards A, B and C."""
    return QuizSession(SequentialMode(make_cards("A", "B", "C")))


def test_ask_questions_exit_word_stops_and_does_not_count_the_question() -> None:
    session = make_session()

    finished = _ask_questions(session, ScriptedInput("a", "exit"), LineRecorder())

    assert finished is False
    assert session.stats().total_questions == 1


def test_ask_questions_returns_true_when_cards_run_out() -> None:
    session = make_session()

    finished = _ask_questions(session, ScriptedInput("a", "b", "c"), LineRecorder())

    assert finished is True
    assert session.stats().total_questions == 3


def test_ask_questions_ctrl_c_adds_an_empty_line_and_stops() -> None:
    session = make_session()
    recorder = LineRecorder()

    finished = _ask_questions(session, ScriptedInput("a", KeyboardInterrupt), recorder)

    assert finished is False
    assert recorder.lines[-1] == ""
    assert session.stats().total_questions == 1


# --- run ---------------------------------------------------------------------


def test_run_sequential_session_with_short_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C"))

    result = run_ui(["-f", "deck.json"], "a", "x", "C")

    assert result.exit_code == 0
    assert result.errors == []
    assert result.prompts == ["> ", "> ", "> "]
    assert result.output == ABC_AXC_LINES + SUMMARY_3_2_B


def test_run_stats_flag_shows_the_full_report_instead_of_the_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C"))

    result = run_ui(["-f", "deck.json", "--stats"], "a", "x", "C")

    assert result.output == ABC_AXC_LINES + REPORT_SEQ_3_2_B
    assert result.output.count(HEAD[1]) == 1
    assert "| Mode               sequential                            |" in (
        result.output
    )


def test_run_adaptive_session_labels_reviews(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C", "D", "E"))

    result = run_ui(["-f", "deck.json", "-m", "Adaptive"], *ADAPTIVE_REPLIES)

    assert result.exit_code == 0
    assert result.output == ADAPTIVE_LINES + SUMMARY_7_4_B


def test_run_adaptive_session_with_stats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C", "D", "E"))

    result = run_ui(["-f", "deck.json", "-m", "Adaptive", "--stats"], *ADAPTIVE_REPLIES)

    assert result.output == ADAPTIVE_LINES + REPORT_ADAPTIVE_7_4_B


def test_run_exit_word_stops_the_quiz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C"))

    result = run_ui(["-f", "deck.json"], "a", "exit")

    assert result.exit_code == 0
    assert result.output == ([*ABC_FEEDBACK_AB, "Quiz stopped.", ""] + SUMMARY_1_1)


def test_run_exit_word_with_stats_reports_a_stopped_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C", "D", "E"))

    result = run_ui(["-f", "deck.json", "-m", "adaptive", "--stats"], "a", "exit")

    assert result.output[-len(REPORT_ADAPTIVE_STOPPED_1_1) :] == (
        REPORT_ADAPTIVE_STOPPED_1_1
    )


def test_run_exit_word_at_the_first_question(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C"))

    result = run_ui(["-f", "deck.json"], "exit")

    assert result.exit_code == 0
    assert result.output == ["Q1: A", "Quiz stopped.", ""] + SUMMARY_0_0


@pytest.mark.parametrize(
    "exception", [KeyboardInterrupt, EOFError], ids=["ctrl-c", "end-of-input"]
)
def test_run_interruption_at_the_second_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exception: type[BaseException]
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C"))

    result = run_ui(["-f", "deck.json"], "a", exception)

    assert result.exit_code == 0
    assert result.output == ([*ABC_FEEDBACK_AB, "", "Quiz stopped.", ""] + SUMMARY_1_1)


@pytest.mark.parametrize(
    "exception", [KeyboardInterrupt, EOFError], ids=["ctrl-c", "end-of-input"]
)
def test_run_interruption_at_the_first_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exception: type[BaseException]
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C"))

    result = run_ui(["-f", "deck.json"], exception)

    assert result.exit_code == 0
    assert result.output == ["Q1: A", "", "Quiz stopped.", ""] + SUMMARY_0_0


def test_run_all_wrong_with_stats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C"))

    result = run_ui(["-f", "deck.json", "--stats"], "x", "x", "x")

    feedback = [result.output[1], result.output[3], result.output[5]]
    assert feedback == [
        red("Incorrect. Answer: a"),
        red("Incorrect. Answer: b"),
        red("Incorrect. Answer: c"),
    ]
    assert result.output[-len(REPORT_SEQ_0_3_ABC) :] == REPORT_SEQ_0_3_ABC


def test_run_all_correct_has_no_missed_terms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C"))

    result = run_ui(["-f", "deck.json"], "a", "b", "c")

    assert result.output[-len(SUMMARY_3_3) :] == SUMMARY_3_3
    assert (
        result.output[-2]
        == "| Missed terms: none                                       |"
    )


def test_run_empty_reply_is_an_incorrect_answer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A"))

    result = run_ui(["-f", "deck.json"], "")

    assert result.output == (
        ["Q1: A", red("Incorrect. Answer: a"), "Quiz finished.", ""] + SUMMARY_1_0_A
    )


def test_run_one_card_deck_answered_correctly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A"))

    result = run_ui(["-f", "deck.json"], "a")

    assert result.exit_code == 0
    assert result.prompts == ["> "]


def test_run_identical_cards_share_the_review_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Identical cards count as the same card for the review label, so the
    # second copy is shown as a review.
    use_deck(tmp_path, monkeypatch, [("Q", "a"), ("Q", "a")])

    result = run_ui(["-f", "deck.json"], "a", "a")

    assert result.output == (
        [
            "Q1: Q",
            green("Correct!"),
            "Q2 (review): Q",
            green("Correct!"),
            "Quiz finished.",
            "",
        ]
        + SUMMARY_2_2
    )


@pytest.mark.parametrize("answer", [" A ", "A"], ids=["with-spaces", "uppercase"])
def test_run_ignores_spaces_and_case_in_answers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, answer: str
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A"))

    result = run_ui(["-f", "deck.json"], answer)

    assert result.output[1] == green("Correct!")


def test_run_object_format_deck_works_like_the_array(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B", "C"), as_object=True)

    result = run_ui(["-f", "deck.json"], "a", "x", "C")

    assert result.output == ABC_AXC_LINES + SUMMARY_3_2_B


def test_run_random_mode_with_a_single_card(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A"))

    result = run_ui(["-f", "deck.json", "-m", "random"], "a")

    assert result.exit_code == 0
    assert result.output[0] == "Q1: A"
    assert "Quiz finished." in result.output


def make_bad_target(kind: str, tmp_path: Path) -> str:
    """Create the file or folder for a load error case and return its path."""
    if kind == "missing":
        return str(tmp_path / "missing.json")
    if kind == "directory":
        return str(tmp_path)
    path = tmp_path / "bad.json"
    if kind == "missing-back":
        path.write_text('[{"front": "A"}]', encoding="utf-8")
    else:
        path.write_text("[", encoding="utf-8")
    return str(path)


@pytest.mark.parametrize(
    ("kind", "expected_start"),
    [
        ("missing", "Error: File not found"),
        ("directory", "Error: Path is a directory"),
        ("missing-back", 'Error: Card 1 is missing the "back" field.'),
        ("invalid-json", "Error: Invalid JSON"),
    ],
)
def test_run_load_errors_return_1_with_one_clean_error_line(
    tmp_path: Path, kind: str, expected_start: str
) -> None:
    result = run_ui(["-f", make_bad_target(kind, tmp_path)])

    assert result.exit_code == 1
    assert len(result.errors) == 1
    assert result.errors[0].startswith(expected_start)
    assert "\n" not in result.errors[0]
    assert "\x1b" not in result.errors[0]
    assert result.output == []
    assert result.prompts == []


def test_run_value_error_from_the_factory_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # This path is defensive: with the current loader and the argparse
    # choices it cannot happen.
    def boom(name: str, cards: list[Flashcard]) -> QuizMode:
        raise ValueError("boom")

    use_deck(tmp_path, monkeypatch, make_pairs("A"))
    monkeypatch.setattr(ui.QuizModeFactory, "create_mode", boom)

    result = run_ui(["-f", "deck.json"])

    assert result.exit_code == 1
    assert result.errors == ["Error: boom"]


# --- run with the real default functions -------------------------------------


def test_run_default_error_function_writes_to_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.json"

    code = ui.run(["-f", str(missing)])

    captured = capsys.readouterr()
    assert code == 1
    assert captured.err == f'Error: File not found: "{missing}".\n'
    assert captured.out == ""


def test_run_default_functions_complete_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B"))
    monkeypatch.setattr("sys.stdin", io.StringIO("a\nx\n"))

    code = ui.run(["-f", "deck.json"])

    expected = (
        "Q1: A\n> "
        + green("Correct!")
        + "\nQ2: B\n> "
        + red("Incorrect. Answer: b")
        + "\nQuiz finished.\n\n"
        + "\n".join(SUMMARY_2_1_B)
        + "\n"
    )
    assert code == 0
    assert capsys.readouterr().out == expected


def test_run_default_functions_end_of_input_stops_the_quiz(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A", "B"))
    monkeypatch.setattr("sys.stdin", io.StringIO("a\n"))

    code = ui.run(["-f", "deck.json"])

    expected = (
        "Q1: A\n> "
        + green("Correct!")
        + "\nQ2: B\n> \n"
        + "Quiz stopped.\n\n"
        + "\n".join(SUMMARY_1_1)
        + "\n"
    )
    assert code == 0
    assert capsys.readouterr().out == expected


# --- main.py -----------------------------------------------------------------


def test_main_script_runs_the_quiz_and_exits_with_code_0(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    use_deck(tmp_path, monkeypatch, make_pairs("A"))
    monkeypatch.setattr("sys.argv", ["main.py", "-f", "deck.json"])
    monkeypatch.setattr("sys.stdin", io.StringIO("a\n"))

    with pytest.raises(SystemExit) as info:
        runpy.run_module("main", run_name="__main__")

    assert info.value.code == 0
    assert "Quiz finished." in capsys.readouterr().out


def test_main_script_exits_with_code_1_when_the_file_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["main.py", "-f", "missing.json"])

    with pytest.raises(SystemExit) as info:
        runpy.run_module("main", run_name="__main__")

    assert info.value.code == 1
    assert "Error: File not found" in capsys.readouterr().err


def test_main_module_does_nothing_when_it_is_only_imported(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runpy.run_module("main", run_name="not_main")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
