"""Unit tests for the sound players in ``sound.py``.

Nothing here makes noise or waits: the writes and the waits are recorded by
small fakes, and the expected values are written by hand.
"""

import inspect
import sys
from collections.abc import Callable
from typing import cast

import pytest

from sound import (
    BELL,
    FAILURE_PAUSES,
    BellPlayer,
    SilentPlayer,
    SoundPlayer,
    create_player,
)


class Events:
    """Records the text written and the waits, in one list.

    Attributes:
        items: Each written text, and ``("sleep", seconds)`` for each wait.
    """

    def __init__(self) -> None:
        """Start with no events."""
        self.items: list[str | tuple[str, float]] = []

    def write(self, text: str) -> None:
        """Record a written text."""
        self.items.append(text)

    def sleep(self, seconds: float) -> None:
        """Record a wait."""
        self.items.append(("sleep", seconds))


class RecordingPlayer(SoundPlayer):
    """A new player: one small class is enough."""

    def __init__(self) -> None:
        """Start with no sounds."""
        self.sounds: list[str] = []

    def play_success(self) -> None:
        """Record a success."""
        self.sounds.append("success")

    def play_failure(self) -> None:
        """Record a failure."""
        self.sounds.append("failure")


class FakeStream:
    """Stand-in for ``sys.stderr`` that records the calls in order."""

    def __init__(self) -> None:
        """Start with no calls."""
        self.calls: list[tuple[str, ...]] = []

    def write(self, text: str) -> None:
        """Record a write."""
        self.calls.append(("write", text))

    def flush(self) -> None:
        """Record a flush."""
        self.calls.append(("flush",))


def returned(method: Callable[[], object]) -> object:
    """Call a method and return what it returned."""
    return method()


# --- SoundPlayer -------------------------------------------------------------


def test_sound_player_is_abstract_with_two_abstract_methods() -> None:
    assert inspect.isabstract(SoundPlayer)
    assert SoundPlayer.__abstractmethods__ == frozenset(
        {"play_success", "play_failure"}
    )


def test_sound_player_cannot_be_created() -> None:
    create = cast(Callable[..., SoundPlayer], SoundPlayer)

    with pytest.raises(TypeError):
        create()


def test_new_subclass_with_both_methods_works() -> None:
    player = RecordingPlayer()

    player.play_success()
    player.play_failure()

    assert player.sounds == ["success", "failure"]


def test_constants() -> None:
    assert BELL == "\a"
    assert FAILURE_PAUSES == (0.12, 0.30)


# --- SilentPlayer ------------------------------------------------------------


def test_silent_player_does_nothing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    waits: list[float] = []
    monkeypatch.setattr("sound.time.sleep", waits.append)
    player = SilentPlayer()

    results = (returned(player.play_success), returned(player.play_failure))

    captured = capsys.readouterr()
    assert results == (None, None)
    assert waits == []
    assert captured.out == ""
    assert captured.err == ""


# --- BellPlayer rings --------------------------------------------------------


def test_bell_player_success_rings_once() -> None:
    events = Events()
    player = BellPlayer(write=events.write, sleep=events.sleep)

    player.play_success()

    assert events.items == ["\a"]


def test_bell_player_failure_rings_three_times_with_the_default_pauses() -> None:
    events = Events()
    player = BellPlayer(write=events.write, sleep=events.sleep)

    player.play_failure()

    assert events.items == ["\a", ("sleep", 0.12), "\a", ("sleep", 0.3), "\a"]


@pytest.mark.parametrize(
    ("pauses", "expected"),
    [
        ((0.5,), ["\a", ("sleep", 0.5), "\a"]),
        ((), ["\a"]),
        ((0,), ["\a", ("sleep", 0), "\a"]),
    ],
    ids=["one-pause", "no-pauses", "zero-pause"],
)
def test_bell_player_rings_are_the_number_of_pauses_plus_one(
    pauses: tuple[float, ...], expected: list[str | tuple[str, float]]
) -> None:
    events = Events()
    player = BellPlayer(write=events.write, sleep=events.sleep, pauses=pauses)

    player.play_failure()

    assert events.items == expected


def test_bell_player_negative_pause_is_rejected() -> None:
    with pytest.raises(ValueError, match="pauses must not be negative"):
        BellPlayer(pauses=(0.1, -0.1))


# --- BellPlayer default functions --------------------------------------------


def test_bell_player_default_write_goes_to_standard_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    player = BellPlayer(sleep=Events().sleep)

    player.play_success()

    captured = capsys.readouterr()
    assert captured.err == "\a"
    assert captured.out == ""


def test_bell_player_default_write_flushes_the_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = FakeStream()
    monkeypatch.setattr(sys, "stderr", stream)
    player = BellPlayer(sleep=Events().sleep)

    player.play_success()

    assert stream.calls == [("write", "\a"), ("flush",)]


def test_bell_player_default_write_does_nothing_without_standard_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stderr", None)
    player = BellPlayer(sleep=Events().sleep)

    result = returned(player.play_success)

    assert result is None


def test_bell_player_default_sleep_is_time_sleep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    waits: list[float] = []
    monkeypatch.setattr("sound.time.sleep", waits.append)
    player = BellPlayer(write=Events().write)

    player.play_failure()

    assert waits == [0.12, 0.3]


# --- BellPlayer errors -------------------------------------------------------


@pytest.mark.parametrize(
    "error", [OSError, ValueError], ids=["os-error", "value-error"]
)
def test_bell_player_write_errors_are_ignored(error: type[Exception]) -> None:
    attempts: list[str] = []
    waits: list[float] = []

    def failing_write(text: str) -> None:
        attempts.append(text)
        raise error("broken output")

    player = BellPlayer(write=failing_write, sleep=waits.append)

    success_result = returned(player.play_success)
    attempts_after_success = len(attempts)
    failure_result = returned(player.play_failure)

    assert success_result is None
    assert failure_result is None
    assert attempts_after_success == 1
    assert len(attempts) == 1 + 3
    assert waits == [0.12, 0.3]


def test_bell_player_keyboard_interrupt_in_sleep_cuts_the_sound() -> None:
    events = Events()
    waits: list[float] = []

    def interrupted_sleep(seconds: float) -> None:
        waits.append(seconds)
        raise KeyboardInterrupt

    player = BellPlayer(write=events.write, sleep=interrupted_sleep)

    result = returned(player.play_failure)

    assert result is None
    assert events.items == ["\a"]
    assert waits == [0.12]


# --- create_player -----------------------------------------------------------


def test_create_player_enabled_returns_a_bell_player() -> None:
    assert type(create_player(True)) is BellPlayer


def test_create_player_disabled_returns_a_silent_player() -> None:
    assert type(create_player(False)) is SilentPlayer
