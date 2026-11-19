"""Shared helpers for the tests of the Flashcard Quizzer.

Import them with ``from tests.helpers import ...``. The ANSI color codes are
written here on purpose and are not imported from ``ui``, so a change of a
color in ``ui.py`` is detected by the tests.
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import ui
from models import Flashcard
from sound import SoundPlayer


def make_cards(*fronts: str) -> list[Flashcard]:
    """Build cards whose back is the front in lowercase.

    Args:
        *fronts: The front of each card.

    Returns:
        The cards, in the given order.
    """
    return [Flashcard(front=front, back=front.lower()) for front in fronts]


def make_pairs(*fronts: str) -> list[tuple[str, str]]:
    """Build ``(front, back)`` pairs whose back is the front in lowercase.

    Args:
        *fronts: The front of each pair.

    Returns:
        The pairs, in the given order.
    """
    return [(front, front.lower()) for front in fronts]


def write_deck(
    directory: Path,
    pairs: Sequence[tuple[str, str]],
    name: str = "deck.json",
    as_object: bool = False,
) -> Path:
    """Write a JSON deck file.

    Args:
        directory: Folder where the file is written.
        pairs: The ``(front, back)`` pairs of the cards.
        name: File name.
        as_object: If True, write ``{"cards": [...]}`` instead of a plain
            JSON array.

    Returns:
        The path of the file that was written.
    """
    cards = [{"front": front, "back": back} for front, back in pairs]
    data: list[dict[str, str]] | dict[str, list[dict[str, str]]]
    data = {"cards": cards} if as_object else cards
    path = directory / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def green(text: str) -> str:
    """Wrap a text in the ANSI green code, as the interface does.

    Args:
        text: The text to color.

    Returns:
        The colored text.
    """
    return "\x1b[32m" + text + "\x1b[0m"


def red(text: str) -> str:
    """Wrap a text in the ANSI red code, as the interface does.

    Args:
        text: The text to color.

    Returns:
        The colored text.
    """
    return "\x1b[31m" + text + "\x1b[0m"


class ScriptedInput:
    """Callable that replaces ``input()`` with scripted replies.

    Attributes:
        prompts: Every prompt received, in order.
    """

    def __init__(self, *replies: str | type[BaseException]) -> None:
        """Store the replies.

        Args:
            *replies: Each reply is a text to return or an exception class to
                raise, for example ``KeyboardInterrupt`` or ``EOFError``.
        """
        self._replies = list(replies)
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        """Record the prompt and return or raise the next reply.

        Args:
            prompt: The prompt shown to the user.

        Returns:
            The next scripted text.

        Raises:
            AssertionError: If no replies are left. An end of input is never
                simulated by itself.
            BaseException: The scripted exception, if the next reply is an
                exception class.
        """
        self.prompts.append(prompt)
        if not self._replies:
            raise AssertionError(
                "The program asked for more input than the test expected."
            )
        reply = self._replies.pop(0)
        if isinstance(reply, str):
            return reply
        raise reply

    @property
    def remaining(self) -> int:
        """Number of replies not used yet."""
        return len(self._replies)


class LineRecorder:
    """Callable that replaces ``print()`` or the error function.

    Attributes:
        lines: Every line received, in order.
    """

    def __init__(self) -> None:
        """Start with no lines."""
        self.lines: list[str] = []

    def __call__(self, line: str) -> None:
        """Store a line.

        Args:
            line: The text received.
        """
        self.lines.append(line)


class RecordingPlayer(SoundPlayer):
    """Sound player that records the sounds instead of playing them.

    Attributes:
        events: ``"sound:success"`` or ``"sound:failure"`` for each sound.
    """

    def __init__(self, events: list[str] | None = None) -> None:
        """Start recording.

        Args:
            events: List where the sounds are recorded, so a test can share
                it with other recorders. A new list is used if it is
                ``None``.
        """
        self.events: list[str] = events if events is not None else []

    def play_success(self) -> None:
        """Record a success sound."""
        self.events.append("sound:success")

    def play_failure(self) -> None:
        """Record a failure sound."""
        self.events.append("sound:failure")


@dataclass(frozen=True)
class RunResult:
    """What happened during a call to ``ui.run``.

    Attributes:
        exit_code: The value returned by ``ui.run``.
        output: The lines sent to the output function.
        errors: The lines sent to the error function.
        prompts: The prompts passed to the input function.
    """

    exit_code: int
    output: list[str]
    errors: list[str]
    prompts: list[str]


def run_ui(
    argv: Sequence[str],
    *replies: str | type[BaseException],
    check_all_used: bool = True,
    sound: SoundPlayer | None = None,
) -> RunResult:
    """Run ``ui.run`` with scripted input and collect what it shows.

    ``SystemExit`` raised by argparse is not caught.

    Args:
        argv: Command line arguments.
        *replies: Scripted replies, as for ``ScriptedInput``.
        check_all_used: If True, assert that every reply was used.
        sound: Sound player passed to ``ui.run``. If it is ``None`` the
            interface creates its own from the ``--sound`` flag.

    Returns:
        The exit code and everything the program showed.

    Raises:
        AssertionError: If ``check_all_used`` is True and some replies were
            not used, or if the program asked for more input than scripted.
    """
    scripted = ScriptedInput(*replies)
    output = LineRecorder()
    errors = LineRecorder()
    exit_code = ui.run(argv, scripted, output, errors, sound=sound)
    if check_all_used:
        assert scripted.remaining == 0, (
            f"{scripted.remaining} scripted replies were not used: "
            "the program asked for less input than the test expected."
        )
    return RunResult(
        exit_code=exit_code,
        output=output.lines,
        errors=errors.lines,
        prompts=scripted.prompts,
    )


@dataclass(frozen=True)
class ParsedReport:
    """The content of a statistics box, read back as data.

    Attributes:
        values: The ``label / value`` rows, by label.
        missed_terms: The missed terms, in the order shown.
    """

    values: dict[str, str]
    missed_terms: list[str]


def _check_report_lines(lines: Sequence[str]) -> None:
    """Check the borders and the shape of every line of a report.

    Args:
        lines: The lines of one box.

    Raises:
        AssertionError: If a border is missing, a line does not have 60
            characters or a line is neither a border nor a row.
    """
    if not lines or not lines[0].startswith("+="):
        raise AssertionError("The report must start with a border")
    if not lines[-1].startswith("+="):
        raise AssertionError("The report must end with a border")
    for line in lines:
        if len(line) != 60:
            raise AssertionError(f"Every line must have 60 characters: {line!r}")
        is_row = line.startswith("| ") and line.endswith(" |")
        if not (line.startswith("+") or is_row):
            raise AssertionError(f"Unexpected line: {line!r}")


def _add_missed_row(missed: list[str], text: str, has_terms: bool) -> None:
    """Add one row of the missed terms section to the list of terms.

    Args:
        missed: The terms read so far, changed in place.
        text: The 56 characters of the row.
        has_terms: False if the section title said that there are none.

    Raises:
        AssertionError: If the row is not allowed at this point.
    """
    if has_terms and text.startswith("  - "):
        missed.append(text[4:].rstrip())
    elif has_terms and text.startswith("    "):
        if not missed:
            raise AssertionError("A continuation row comes before any term")
        missed[-1] += " " + text.strip()
    else:
        raise AssertionError(f"Unexpected row in the missed terms: {text!r}")


def parse_report(lines: Sequence[str]) -> ParsedReport:
    """Read the lines of one statistics box.

    It does not use anything from ``ui``, so it checks the box from the
    outside. The title row is skipped. Wrapped terms are joined with one
    space, which is exact when the wrap happens at a space (true for the
    real decks).

    Args:
        lines: The lines of ONE box, from the first border to the last.

    Returns:
        The label/value rows and the missed terms.

    Raises:
        AssertionError: If the lines are not a well formed box.
    """
    _check_report_lines(lines)
    rows = [line[2:58] for line in lines if line.startswith("| ")][1:]
    values: dict[str, str] = {}
    missed: list[str] = []
    in_missed_section = False
    has_terms = False
    for text in rows:
        if in_missed_section:
            _add_missed_row(missed, text, has_terms)
        elif text.startswith("Missed terms"):
            in_missed_section = True
            has_terms = text.strip() != "Missed terms: none"
        else:
            label = text[:19].strip()
            if label in values:
                raise AssertionError(f"Duplicate label: {label!r}")
            values[label] = text[19:].strip()
    if not in_missed_section:
        raise AssertionError("The report has no missed terms section")
    return ParsedReport(values, missed)
