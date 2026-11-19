"""Tests for the intro banner: its data, its layout and when it is shown.

The expected banner is built from ``BANNER_PLAIN``, a literal written by hand,
and the color helpers of ``tests.helpers``, never with functions from ``ui``.
"""

import io
import re
import runpy
from pathlib import Path

import pytest

import banner
import ui
from tests.helpers import (
    LineRecorder,
    ScriptedInput,
    green,
    make_pairs,
    write_deck,
    yellow,
)
from ui import _banner_lines

BANNER_PLAIN = [
    "+==========================================================+",
    "|                                                          |",
    "|  ##### #      ###   #### #   #  ####  ###  ####  ####    |",
    "|  #     #     #   # #     #   # #     #   # #   # #   #   |",
    "|  ####  #     #####  ###  ##### #     ##### ####  #   #   |",
    "|  #     #     #   #     # #   # #     #   # #  #  #   #   |",
    "|  #     ##### #   # ####  #   #  #### #   # #   # ####    |",
    "|                                                          |",
    "|         ###  #   # ##### ##### ##### ##### ####          |",
    "|        #   # #   #   #      #     #  #     #   #         |",
    "|        # # # #   #   #     #     #   ####  ####          |",
    "|        #  #  #   #   #    #     #    #     #  #          |",
    "|         ## #  ###  ##### ##### ##### ##### #   #         |",
    "|                                                          |",
    "|               LEARN IT. QUIZ IT. BEAT IT.                |",
    "|              SEQUENTIAL * RANDOM * ADAPTIVE              |",
    "+----------------------------------------------------------+",
    "|        READY PLAYER 1   MODE: ADAPTIVE   CARDS: 8        |",
    "+==========================================================+",
]
ART_ROWS = tuple(range(2, 7)) + tuple(range(8, 13))
GREEN_CODE = "\x1b[32m"
YELLOW_CODE = "\x1b[33m"
RED_CODE = "\x1b[31m"
FIRST_LINE = green("+" + "=" * 58 + "+")


def strip_codes(line: str) -> str:
    """Remove the ANSI escape sequences of a line."""
    return re.sub(r"\x1b\[\d+m", "", line)


def expected_banner() -> list[str]:
    """Build the expected colored lines from the plain literal."""
    lines: list[str] = []
    for index, plain in enumerate(BANNER_PLAIN):
        if index in ART_ROWS:
            lines.append(green("| ") + yellow(plain[2:58]) + green(" |"))
        else:
            lines.append(green(plain))
    return lines


# --- Data of banner.py -------------------------------------------------------


@pytest.mark.parametrize("name", ["ART_FIRST", "ART_SECOND"])
def test_art_has_five_rows_of_56_characters_with_only_spaces_and_hashes(
    name: str,
) -> None:
    art: tuple[str, ...] = getattr(banner, name)

    assert len(art) == 5
    assert {len(row) for row in art} == {56}
    assert all(set(row) <= {" ", "#"} for row in art)


@pytest.mark.parametrize("name", ["TAGLINE", "MODES_LINE", "STATUS_FORMAT"])
def test_banner_texts_are_ascii(name: str) -> None:
    text: str = getattr(banner, name)

    assert text.isascii()


@pytest.mark.parametrize("name", ["TAGLINE", "MODES_LINE"])
def test_banner_small_texts_fit_in_a_row(name: str) -> None:
    text: str = getattr(banner, name)

    assert len(text) <= 56


# --- Layout ------------------------------------------------------------------


def test_banner_lines_match_the_expected_colored_banner() -> None:
    assert _banner_lines("adaptive", 8) == expected_banner()


def test_banner_has_19_lines_of_60_ascii_characters() -> None:
    lines = [strip_codes(line) for line in _banner_lines("adaptive", 8)]

    assert len(lines) == 19
    assert {len(line) for line in lines} == {60}
    assert all(ord(char) < 128 for line in lines for char in line)


def test_banner_without_codes_equals_the_plain_literal() -> None:
    lines = [strip_codes(line) for line in _banner_lines("adaptive", 8)]

    assert lines == BANNER_PLAIN


# --- Colors ------------------------------------------------------------------


def test_banner_frame_is_green_and_only_the_art_is_yellow() -> None:
    lines = _banner_lines("adaptive", 8)

    assert all(line.startswith(GREEN_CODE) for line in lines)
    with_yellow = [i for i, line in enumerate(lines) if YELLOW_CODE in line]
    assert with_yellow == list(ART_ROWS)


def test_banner_has_no_red() -> None:
    lines = _banner_lines("adaptive", 8)

    assert not any(RED_CODE in line for line in lines)


# --- Status line -------------------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "cards", "plain"),
    [
        (
            "sequential",
            236,
            "|      READY PLAYER 1   MODE: SEQUENTIAL   CARDS: 236      |",
        ),
        (
            "random",
            10,
            "|        READY PLAYER 1   MODE: RANDOM   CARDS: 10         |",
        ),
    ],
    ids=["sequential-236", "random-10"],
)
def test_banner_status_line_shows_the_mode_and_the_cards(
    mode: str, cards: int, plain: str
) -> None:
    assert _banner_lines(mode, cards)[17] == green(plain)


# --- run ---------------------------------------------------------------------


def test_run_does_not_show_the_banner_by_default(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B"))
    output = LineRecorder()

    ui.run(["-f", str(path)], ScriptedInput("a", "b"), output, LineRecorder())

    assert output.lines[0] == "Q1: A"
    assert not any("READY PLAYER 1" in line for line in output.lines)


def test_run_with_banner_shows_it_before_the_first_question(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B", "C", "D", "E", "F", "G", "H"))
    output = LineRecorder()

    code = ui.run(
        ["-m", "adaptive", "-f", str(path)],
        ScriptedInput("exit"),
        output,
        LineRecorder(),
        banner=True,
    )

    assert code == 0
    assert output.lines[:19] == expected_banner()
    assert output.lines[19] == ""
    assert output.lines[20] == "Q1: A"


def test_run_with_banner_does_not_show_it_when_the_file_is_missing(
    tmp_path: Path,
) -> None:
    output = LineRecorder()
    errors = LineRecorder()

    code = ui.run(
        ["-f", str(tmp_path / "missing.json")],
        ScriptedInput(),
        output,
        errors,
        banner=True,
    )

    assert code == 1
    assert output.lines == []
    assert errors.lines[0].startswith("Error: File not found")


def test_run_with_banner_shows_it_only_after_the_deck_was_loaded(
    tmp_path: Path,
) -> None:
    path = tmp_path / "deck.json"
    path.write_text('[{"front": "A"}]', encoding="utf-8")
    output = LineRecorder()
    errors = LineRecorder()

    code = ui.run(["-f", str(path)], ScriptedInput(), output, errors, banner=True)

    assert code == 1
    assert output.lines == []
    assert errors.lines[0].startswith("Error: Card 1 is missing")


# --- main.py -----------------------------------------------------------------


def test_main_script_shows_the_banner_before_the_quiz(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_deck(tmp_path, make_pairs("A"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["main.py", "-f", "deck.json"])
    monkeypatch.setattr("sys.stdin", io.StringIO("a\n"))

    with pytest.raises(SystemExit) as info:
        runpy.run_module("main", run_name="__main__")

    out = capsys.readouterr().out
    assert info.value.code == 0
    assert out.splitlines()[0] == FIRST_LINE
    assert "READY PLAYER 1   MODE: SEQUENTIAL   CARDS: 1" in out
    assert "Quiz finished." in out


def test_main_script_help_does_not_show_the_banner(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["main.py", "--help"])

    with pytest.raises(SystemExit) as info:
        runpy.run_module("main", run_name="__main__")

    assert info.value.code == 0
    assert "READY PLAYER 1" not in capsys.readouterr().out


def test_main_script_load_error_does_not_show_the_banner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["main.py", "-f", "missing.json"])

    with pytest.raises(SystemExit) as info:
        runpy.run_module("main", run_name="__main__")

    captured = capsys.readouterr()
    assert info.value.code == 1
    assert "READY PLAYER 1" not in captured.out
    assert "Error: File not found" in captured.err
