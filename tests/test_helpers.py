"""Unit tests for the shared helpers in ``tests/helpers.py``."""

from pathlib import Path

import pytest

from data_loader import load_flashcards
from models import Flashcard
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
