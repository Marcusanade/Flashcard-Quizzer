"""Sound feedback for the console interface.

Design: ``SoundPlayer`` is an abstract strategy with one method for a correct
answer and one for an incorrect answer. ``SilentPlayer`` does nothing and is a
null object, so the interface needs no ``if`` to know whether sound is
enabled. ``BellPlayer`` rings the terminal bell: one ring for a correct answer
and three rings, with silences between them, for an incorrect one. The rings
go to the standard error stream, so a redirected output file does not fill
with control characters. Sound never breaks a quiz: write errors are ignored.
"""

import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence

BELL = "\a"
FAILURE_PAUSES = (0.12, 0.30)


class SoundPlayer(ABC):
    """Abstract strategy that plays the sound of an answer."""

    @abstractmethod
    def play_success(self) -> None:
        """Play the sound of a correct answer."""

    @abstractmethod
    def play_failure(self) -> None:
        """Play the sound of an incorrect answer."""


class SilentPlayer(SoundPlayer):
    """Player that does nothing. It is the default of the program."""

    def play_success(self) -> None:
        """Do nothing."""

    def play_failure(self) -> None:
        """Do nothing."""


def _write_to_stderr(text: str) -> None:
    """Write a text to the standard error stream and flush it.

    The stream is looked up when the function is called, not when the module
    is imported.

    Args:
        text: The text to write.
    """
    stream = sys.stderr
    if stream is None:
        return
    stream.write(text)
    stream.flush()


class BellPlayer(SoundPlayer):
    """Player that rings the terminal bell.

    The bell cannot change its pitch or its length, so the incorrect answer
    is made of rings with silences between them.
    """

    def __init__(
        self,
        write: Callable[[str], None] | None = None,
        sleep: Callable[[float], None] | None = None,
        pauses: Sequence[float] = FAILURE_PAUSES,
    ) -> None:
        """Create a player.

        Args:
            write: Function that writes the bell. The standard error stream
                is used if it is ``None``.
            sleep: Function that waits some seconds. ``time.sleep`` is used
                if it is ``None``.
            pauses: Seconds to wait before each ring after the first one in
                the failure sound.

        Raises:
            ValueError: If a pause is negative.
        """
        if any(pause < 0 for pause in pauses):
            raise ValueError("pauses must not be negative.")
        self._write = write if write is not None else _write_to_stderr
        self._sleep = sleep if sleep is not None else time.sleep
        self._pauses = tuple(pauses)

    def play_success(self) -> None:
        """Ring the bell once."""
        self._ring()

    def play_failure(self) -> None:
        """Ring the bell, then wait and ring again for each pause.

        The number of rings is the number of pauses plus one.
        """
        self._ring()
        try:
            for pause in self._pauses:
                self._sleep(pause)
                self._ring()
        except KeyboardInterrupt:
            # A Ctrl+C that arrives in the middle of a short sound only cuts
            # the sound. The user can press it again at the prompt.
            return

    def _ring(self) -> None:
        """Write one bell, ignoring the errors of the output."""
        try:
            self._write(BELL)
        except (OSError, ValueError):
            pass


def create_player(enabled: bool) -> SoundPlayer:
    """Create the player for the sound option.

    Args:
        enabled: True to ring the bell, False for silence.

    Returns:
        A new ``BellPlayer`` or a new ``SilentPlayer``.
    """
    if enabled:
        return BellPlayer()
    return SilentPlayer()
