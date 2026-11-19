"""Unit tests for the shared helpers in ``tests/helpers.py``."""

from pathlib import Path

import pytest

from data_loader import load_flashcards
from models import Flashcard
from tests.helpers import (
    LineRecorder,
    ParsedReport,
    ScriptedInput,
    green,
    make_cards,
    make_pairs,
    parse_report,
    red,
    run_ui,
    write_deck,
)

# --- make_cards and make_pairs -----------------------------------------------


def test_make_cards_uses_lowercase_front_as_back() -> None:
    cards = make_cards("A", "Bc")

    assert cards == [Flashcard("A", "a"), Flashcard("Bc", "bc")]


def test_make_cards_without_arguments_is_empty() -> None:
    assert make_cards() == []


def test_make_pairs_uses_lowercase_front_as_back() -> None:
    pairs = make_pairs("C", "A", "B")

    assert pairs == [("C", "c"), ("A", "a"), ("B", "b")]


def test_make_pairs_without_arguments_is_empty() -> None:
    assert make_pairs() == []


# --- write_deck --------------------------------------------------------------


@pytest.mark.parametrize("as_object", [False, True], ids=["array", "object"])
def test_write_deck_formats_load_into_expected_cards(
    tmp_path: Path, as_object: bool
) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B"), as_object=as_object)

    cards = load_flashcards(path)

    assert cards == make_cards("A", "B")


def test_write_deck_writes_utf8_text(tmp_path: Path) -> None:
    path = write_deck(tmp_path, [("ñ", "é")])

    text = path.read_text(encoding="utf-8")

    assert "ñ" in text
    assert load_flashcards(path) == [Flashcard("ñ", "é")]


def test_write_deck_returns_the_path_of_the_written_file(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A"))

    assert path == tmp_path / "deck.json"
    assert path.is_file()


def test_write_deck_uses_custom_name(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A"), name="other.json")

    assert path.name == "other.json"
    assert path.is_file()


# --- green and red -----------------------------------------------------------


def test_green_wraps_text_in_green_code() -> None:
    assert green("x") == "\x1b[32mx\x1b[0m"


def test_red_wraps_text_in_red_code() -> None:
    assert red("x") == "\x1b[31mx\x1b[0m"


# --- ScriptedInput -----------------------------------------------------------


def test_scripted_input_returns_replies_in_order() -> None:
    scripted = ScriptedInput("a", "b")

    first = scripted("> ")
    second = scripted("> ")

    assert (first, second) == ("a", "b")


def test_scripted_input_records_every_prompt() -> None:
    scripted = ScriptedInput("a", "b")

    scripted("first> ")
    scripted("second> ")

    assert scripted.prompts == ["first> ", "second> "]


@pytest.mark.parametrize(
    "exception",
    [KeyboardInterrupt, EOFError],
    ids=["keyboard-interrupt", "eof"],
)
def test_scripted_input_raises_scripted_exception(
    exception: type[BaseException],
) -> None:
    scripted = ScriptedInput(exception)

    with pytest.raises(exception):
        scripted("> ")


def test_scripted_input_without_replies_raises_assertion_error() -> None:
    scripted = ScriptedInput("a")
    scripted("> ")

    with pytest.raises(AssertionError, match="more input"):
        scripted("> ")


def test_scripted_input_records_the_prompt_even_when_it_runs_out() -> None:
    scripted = ScriptedInput()

    with pytest.raises(AssertionError):
        scripted("> ")

    assert scripted.prompts == ["> "]


def test_scripted_input_remaining_counts_down() -> None:
    scripted = ScriptedInput("a", "b")
    before = scripted.remaining

    scripted("> ")
    after_one = scripted.remaining
    scripted("> ")

    assert (before, after_one, scripted.remaining) == (2, 1, 0)


# --- LineRecorder ------------------------------------------------------------


def test_line_recorder_stores_lines_in_order() -> None:
    recorder = LineRecorder()

    recorder("one")
    recorder("two")

    assert recorder.lines == ["one", "two"]


# --- run_ui ------------------------------------------------------------------


def test_run_ui_complete_session(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B"))

    result = run_ui(["-f", str(path)], "a", "b")

    assert result.exit_code == 0
    assert result.output[:5] == [
        "Q1: A",
        green("Correct!"),
        "Q2: B",
        green("Correct!"),
        "Quiz finished.",
    ]
    assert result.errors == []
    assert result.prompts == ["> ", "> "]


def test_run_ui_missing_file_reports_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"

    result = run_ui(["-f", str(missing)])

    assert result.exit_code == 1
    assert len(result.errors) == 1
    assert result.errors[0].startswith("Error: File not found")
    assert result.output == []


def test_run_ui_unused_reply_raises_assertion_error(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A"))

    with pytest.raises(AssertionError, match="not used"):
        run_ui(["-f", str(path)], "a", "extra")


def test_run_ui_unused_reply_is_allowed_when_check_is_disabled(
    tmp_path: Path,
) -> None:
    path = write_deck(tmp_path, make_pairs("A"))

    result = run_ui(["-f", str(path)], "a", "extra", check_all_used=False)

    assert result.exit_code == 0


def test_run_ui_help_raises_system_exit_zero() -> None:
    with pytest.raises(SystemExit) as info:
        run_ui(["--help"])

    assert info.value.code == 0


# --- parse_report ------------------------------------------------------------

HEAD = [
    "+==========================================================+",
    "|                      SESSION REPORT                      |",
    "+==========================================================+",
]
DASH = "+----------------------------------------------------------+"
END = "+==========================================================+"
BOX_SUMMARY_3_2_B = (
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
BOX_SUMMARY_0_0 = (
    HEAD
    + [
        "| Total questions    0                                     |",
        "| Accuracy           [--------------------]   0.0%         |",
        "| Rank               -                                     |",
    ]
    + [DASH]
    + ["| Missed terms: none                                       |"]
    + [END]
)
BOX_SUMMARY_WRAPPED = (
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
BOX_REPORT_SEQ_3_2_B = (
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
BOX_REPORT_ABC = (
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
CONTINUATION_ROW = "|     block?                                               |"
HELLO_ROW = "| hello                                                    |"
TERM_B_ROW = "|   - B                                                    |"
SHORT_LINE = "| Total questions    3                                    |"
BAD_START_LINE = "x Total questions    3                                     |"


def test_parse_report_summary_with_one_missed_term() -> None:
    report = parse_report(BOX_SUMMARY_3_2_B)

    assert report == ParsedReport(
        {
            "Total questions": "3",
            "Accuracy": "[#############-------]  66.7%",
            "Rank": "C",
        },
        ["B"],
    )


def test_parse_report_summary_without_missed_terms() -> None:
    report = parse_report(BOX_SUMMARY_0_0)

    assert report == ParsedReport(
        {
            "Total questions": "0",
            "Accuracy": "[--------------------]   0.0%",
            "Rank": "-",
        },
        [],
    )


def test_parse_report_joins_a_wrapped_term_with_one_space() -> None:
    report = parse_report(BOX_SUMMARY_WRAPPED)

    assert report == ParsedReport(
        {
            "Total questions": "9",
            "Accuracy": "[##################--]  88.9%",
            "Rank": "B",
        },
        ["Which keyword handles an exception raised in a try block?"],
    )


def test_parse_report_full_report_has_the_nine_values() -> None:
    report = parse_report(BOX_REPORT_SEQ_3_2_B)

    assert report == ParsedReport(
        {
            "Mode": "sequential",
            "Deck file": "deck.json",
            "Deck size": "3",
            "Session": "finished",
            "Total questions": "3",
            "Correct answers": "2",
            "Incorrect answers": "1",
            "Accuracy": "[#############-------]  66.7%",
            "Rank": "C",
        },
        ["B"],
    )


def test_parse_report_keeps_the_order_of_the_missed_terms() -> None:
    report = parse_report(BOX_REPORT_ABC)

    assert report.missed_terms == ["A", "B", "C"]


@pytest.mark.parametrize(
    ("lines", "message"),
    [
        ([], "must start with a border"),
        (BOX_SUMMARY_3_2_B[1:], "must start with a border"),
        (BOX_SUMMARY_3_2_B[:-1], "must end with a border"),
        (
            BOX_SUMMARY_3_2_B[:3] + [SHORT_LINE] + BOX_SUMMARY_3_2_B[4:],
            "must have 60 characters",
        ),
        (
            BOX_SUMMARY_3_2_B[:3] + [BAD_START_LINE] + BOX_SUMMARY_3_2_B[4:],
            "Unexpected line",
        ),
        (
            BOX_SUMMARY_3_2_B[:6] + [BOX_SUMMARY_3_2_B[5]] + BOX_SUMMARY_3_2_B[6:],
            "Duplicate label",
        ),
        (
            BOX_SUMMARY_3_2_B[:7] + BOX_SUMMARY_3_2_B[8:],
            "no missed terms section",
        ),
        (
            BOX_SUMMARY_3_2_B[:8] + [CONTINUATION_ROW] + BOX_SUMMARY_3_2_B[8:],
            "continuation",
        ),
        (
            BOX_SUMMARY_3_2_B[:8] + [HELLO_ROW] + BOX_SUMMARY_3_2_B[8:],
            "Unexpected row in the missed terms",
        ),
        (
            BOX_SUMMARY_0_0[:-1] + [TERM_B_ROW] + BOX_SUMMARY_0_0[-1:],
            "Unexpected row in the missed terms",
        ),
    ],
    ids=[
        "empty",
        "no-first-border",
        "no-last-border",
        "short-line",
        "bad-first-character",
        "duplicate-label",
        "no-missed-section",
        "continuation-before-term",
        "unexpected-row",
        "term-after-none",
    ],
)
def test_parse_report_rejects_malformed_boxes(lines: list[str], message: str) -> None:
    with pytest.raises(AssertionError, match=message):
        parse_report(lines)


def test_parse_report_label_column_is_19_characters_wide() -> None:
    row = "| ABCDEFGHIJKLMNOPQRSvalue                                 |"
    lines = BOX_SUMMARY_0_0[:3] + [row] + BOX_SUMMARY_0_0[-2:]

    report = parse_report(lines)

    assert report == ParsedReport({"ABCDEFGHIJKLMNOPQRS": "value"}, [])
