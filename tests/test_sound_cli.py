"""Tests for the ``--sound`` option and the connection with the interface.

The sounds are recorded by a ``RecordingPlayer``, except in the tests that use
the real ``BellPlayer``: those capture the standard error stream and replace
``time.sleep``, so nothing rings and nothing waits.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import ui
from quiz_engine import QuizSession, SequentialMode
from tests.helpers import (
    PROJECT_ROOT,
    LineRecorder,
    RecordingPlayer,
    ScriptedInput,
    green,
    make_cards,
    make_pairs,
    red,
    run_ui,
    write_deck,
)
from ui import _ask_questions, build_parser

# --- Parser ------------------------------------------------------------------


def test_parser_sound_defaults_to_false() -> None:
    args = build_parser().parse_args(["-f", "deck.json"])

    assert args.sound is False


def test_parser_sound_flag_is_true() -> None:
    args = build_parser().parse_args(["-f", "deck.json", "--sound"])

    assert args.sound is True


def test_parser_help_lists_the_sound_option(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--help"])

    assert "--sound" in capsys.readouterr().out


# --- _ask_questions ----------------------------------------------------------


def test_ask_questions_plays_a_sound_for_each_answer() -> None:
    session = QuizSession(SequentialMode(make_cards("A", "B")))
    player = RecordingPlayer()

    finished = _ask_questions(session, ScriptedInput("a", "x"), LineRecorder(), player)

    assert player.events == ["sound:success", "sound:failure"]
    assert finished is True


# --- Injected player ---------------------------------------------------------


def test_injected_player_hears_every_answer(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B", "C"))
    player = RecordingPlayer()

    run_ui(["-f", str(path)], "a", "x", "c", sound=player)

    assert player.events == ["sound:success", "sound:failure", "sound:success"]


def test_sound_does_not_change_what_is_printed(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B", "C"))

    with_player = run_ui(["-f", str(path)], "a", "x", "c", sound=RecordingPlayer())
    without_player = run_ui(["-f", str(path)], "a", "x", "c")

    assert with_player.output == without_player.output


def test_sound_comes_after_the_feedback_and_not_after_the_questions(
    tmp_path: Path,
) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B", "C"))
    timeline: list[str] = []

    ui.run(
        ["-f", str(path)],
        ScriptedInput("a", "x", "c"),
        timeline.append,
        LineRecorder(),
        RecordingPlayer(timeline),
    )

    assert timeline[:11] == [
        "Q1: A",
        green("Correct!"),
        "sound:success",
        "Q2: B",
        red("Incorrect. Answer: b"),
        "sound:failure",
        "Q3: C",
        green("Correct!"),
        "sound:success",
        "Quiz finished.",
        "",
    ]
    assert len([item for item in timeline if item.startswith("sound:")]) == 3


# --- Quitting and special answers --------------------------------------------


@pytest.mark.parametrize(
    "quit_reply",
    ["exit", KeyboardInterrupt, EOFError],
    ids=["exit-word", "ctrl-c", "end-of-input"],
)
def test_no_sound_when_the_user_quits(
    tmp_path: Path, quit_reply: str | type[BaseException]
) -> None:
    path = write_deck(tmp_path, make_pairs("A", "B", "C"))
    player = RecordingPlayer()

    run_ui(["-f", str(path)], "a", quit_reply, sound=player)

    assert player.events == ["sound:success"]


def test_empty_reply_rings_the_failure_sound(tmp_path: Path) -> None:
    path = write_deck(tmp_path, make_pairs("A"))
    player = RecordingPlayer()

    run_ui(["-f", str(path)], "", sound=player)

    assert player.events == ["sound:failure"]


# --- The real bell -----------------------------------------------------------


def test_sound_flag_rings_the_real_bell_on_standard_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    waits: list[float] = []
    monkeypatch.setattr("sound.time.sleep", waits.append)
    path = write_deck(tmp_path, make_pairs("A", "B", "C"))

    result = run_ui(["-f", str(path), "--sound", "--limit", "2"], "a", "x")

    assert capsys.readouterr().err == "\a" * 4
    assert waits == [0.12, 0.3]
    assert not any("\a" in line for line in result.output)


def test_without_the_flag_nothing_rings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    waits: list[float] = []
    monkeypatch.setattr("sound.time.sleep", waits.append)
    path = write_deck(tmp_path, make_pairs("A", "B", "C"))

    run_ui(["-f", str(path), "--limit", "2"], "a", "x")

    assert capsys.readouterr().err == ""
    assert waits == []


def test_injected_player_wins_over_the_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_deck(tmp_path, make_pairs("A"))
    player = RecordingPlayer()

    run_ui(["-f", str(path), "--sound"], "a", sound=player)

    assert player.events == ["sound:success"]
    assert capsys.readouterr().err == ""


def test_load_error_does_not_ring(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.json"

    result = run_ui(["-f", str(missing), "--sound"])

    assert result.exit_code == 1
    assert result.errors[0].startswith("Error: File not found")
    assert capsys.readouterr().err == ""


# --- Separate process --------------------------------------------------------


def test_main_script_with_sound_rings_the_bell_on_standard_error() -> None:
    # The bell goes to the standard error, so the standard output stays clean.
    # The failure sound really waits about 0.4 seconds. This test does not
    # count for the coverage because it runs in another process.
    completed = subprocess.run(
        [
            sys.executable,
            "main.py",
            "-f",
            "data/glossary.json",
            "--limit",
            "2",
            "--sound",
        ],
        input="Application Programming Interface\nx\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=PROJECT_ROOT,
        timeout=30,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    assert completed.returncode == 0
    assert completed.stderr == "\a" * 4
    assert "\a" not in completed.stdout
    assert "Quiz finished." in completed.stdout
