"""Console interface for the Flashcard Quizzer.

This module reads the command line arguments, loads the deck, runs the quiz
loop and prints the messages. The quiz logic lives in ``quiz_engine`` and the
deck loading in ``data_loader``: this module only talks to the user.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from data_loader import FlashcardLoadError, load_flashcards
from models import Flashcard
from quiz_engine import AnswerResult, QuizModeFactory, QuizSession, SessionStats

EXIT_OK = 0
EXIT_LOAD_ERROR = 1

TABLE_HEADER = ("Statistic", "Value")

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"

EXIT_WORD = "exit"


@dataclass(frozen=True)
class ReadResult:
    """What the user did when asked for an answer.

    A small dataclass is clearer than a tuple because both fields have a
    name.

    Attributes:
        answer: The text typed by the user, or ``None`` if the user wants to
            quit.
        interrupted: True if the user quit with Ctrl+C or by closing the
            input, so the cursor is left after the prompt. False if the user
            typed the exit word or gave a normal answer.
    """

    answer: str | None
    interrupted: bool


def _print_error(message: str) -> None:
    """Write an error message to the standard error stream.

    Args:
        message: The text to write.
    """
    print(message, file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser.

    Returns:
        The parser. Invalid arguments and ``--help`` make argparse raise
        ``SystemExit``, which is not caught here.
    """
    modes = QuizModeFactory.available_modes()
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Quiz yourself with flashcards loaded from a JSON deck.",
    )
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help="path of the JSON deck to load",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=modes,
        default="sequential",
        type=str.lower,
        help=f"quiz mode: {', '.join(modes)} (default: %(default)s)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="show the full statistics report at the end",
    )
    return parser


def _question_label(number: int, is_review: bool) -> str:
    """Build the label of a question.

    Args:
        number: Question number, counting every time a card is asked.
        is_review: Whether the card was already asked in this session.

    Returns:
        ``Q5`` or ``Q5 (review)``.
    """
    return f"Q{number} (review)" if is_review else f"Q{number}"


def _question_line(number: int, card: Flashcard, is_review: bool) -> str:
    """Build the line that shows a question.

    Args:
        number: Question number, counting every time a card is asked.
        card: The card being asked.
        is_review: Whether the card was already asked in this session.

    Returns:
        The text to show, for example ``Q1: What is a list?``.
    """
    return f"{_question_label(number, is_review)}: {card.front}"


def _colorize(text: str, color: str) -> str:
    """Wrap a text in an ANSI color.

    Args:
        text: The text to color.
        color: The ANSI escape code that starts the color.

    Returns:
        The text between the color code and the reset code.
    """
    return color + text + RESET


def _feedback_line(result: AnswerResult) -> str:
    """Build the feedback shown after an answer.

    Args:
        result: The outcome of the answer.

    Returns:
        ``Correct!`` in green or ``Incorrect. Answer: <expected>`` in red.
    """
    if result.correct:
        return _colorize("Correct!", GREEN)
    return _colorize(f"Incorrect. Answer: {result.expected}", RED)


def _read_answer(input_fn: Callable[[str], str]) -> ReadResult:
    """Read one answer and detect when the user wants to quit.

    This is the only place that handles Ctrl+C and the end of the input. It
    prints nothing itself: the caller decides what to show, using
    ``ReadResult.interrupted``.

    Known limitation: the word "exit" is reserved. A card whose correct
    answer is literally "exit" cannot be answered correctly.

    Args:
        input_fn: Function used to read the answer. The prompt is ``> ``.

    Returns:
        The answer, or a result with ``answer=None`` when the user typed the
        exit word (ignoring spaces and letter case), pressed Ctrl+C or closed
        the input.
    """
    try:
        text = input_fn("> ")
    except (KeyboardInterrupt, EOFError):
        return ReadResult(answer=None, interrupted=True)
    if text.strip().casefold() == EXIT_WORD:
        return ReadResult(answer=None, interrupted=False)
    return ReadResult(answer=text, interrupted=False)


def _ask_questions(
    session: QuizSession,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> bool:
    """Ask questions until the session has no more cards or the user quits.

    A question that was shown but not answered is not counted. If the user
    quits with Ctrl+C or by closing the input, an empty line is shown first
    so the next message starts on a new line.

    Args:
        session: The quiz session.
        input_fn: Function used to read an answer.
        output_fn: Function used to show a message.

    Returns:
        True if the session ran out of cards, False if the user quit.
    """
    # Two identical cards in a deck are equal, so for the "(review)" label
    # they count as the same card.
    asked: set[Flashcard] = set()
    number = 0
    while (card := session.next_question()) is not None:
        number += 1
        output_fn(_question_line(number, card, card in asked))
        asked.add(card)
        reply = _read_answer(input_fn)
        if reply.answer is None:
            if reply.interrupted:
                output_fn("")
            return False
        output_fn(_feedback_line(session.submit_answer(reply.answer)))
    return True


def _format_table(rows: Sequence[tuple[str, str]]) -> list[str]:
    """Build a two-column ASCII table.

    Each column is as wide as its longest text, header included.

    Args:
        rows: The data rows, as pairs of texts. The header row is added.

    Returns:
        The lines of the table: border, header, border, rows, border.
    """
    width1 = max(len(first) for first, _ in (TABLE_HEADER, *rows))
    width2 = max(len(second) for _, second in (TABLE_HEADER, *rows))
    border = "+" + "-" * (width1 + 2) + "+" + "-" * (width2 + 2) + "+"

    def row_line(first: str, second: str) -> str:
        """Format one table row."""
        return f"| {first.ljust(width1)} | {second.ljust(width2)} |"

    lines = [border, row_line(*TABLE_HEADER), border]
    lines.extend(row_line(first, second) for first, second in rows)
    lines.append(border)
    return lines


def _missed_terms_lines(missed: Sequence[str]) -> list[str]:
    """Build the lines that list the missed terms.

    Args:
        missed: The missed terms, in order of first miss.

    Returns:
        ``Missed terms: none`` if there are none, otherwise a title line
        followed by one ``  - <term>`` line per term.
    """
    if not missed:
        return ["Missed terms: none"]
    return ["Missed terms:", *(f"  - {term}" for term in missed)]


def _accuracy_text(stats: SessionStats) -> str:
    """Format the accuracy with one decimal.

    Args:
        stats: The session statistics.

    Returns:
        For example ``66.7%``.
    """
    return f"{stats.accuracy_percent:.1f}%"


def _summary_lines(stats: SessionStats) -> list[str]:
    """Build the short summary shown at the end of the quiz.

    Args:
        stats: The session statistics.

    Returns:
        The table with the total questions and the accuracy, followed by the
        missed terms.
    """
    rows = [
        ("Total questions", str(stats.total_questions)),
        ("Accuracy", _accuracy_text(stats)),
    ]
    return _format_table(rows) + _missed_terms_lines(stats.missed_terms)


def _report_lines(
    stats: SessionStats,
    mode: str,
    deck_file: str,
    deck_size: int,
    finished: bool,
) -> list[str]:
    """Build the full statistics report shown with ``--stats``.

    Args:
        stats: The session statistics.
        mode: Name of the quiz mode, in lowercase.
        deck_file: The deck path, as the user typed it.
        deck_size: Number of cards in the deck.
        finished: True if the cards ran out, False if the user quit.

    Returns:
        The table with all the rows, followed by the missed terms.
    """
    rows = [
        ("Mode", mode),
        ("Deck file", deck_file),
        ("Deck size", str(deck_size)),
        ("Session", "finished" if finished else "stopped"),
        ("Total questions", str(stats.total_questions)),
        ("Correct answers", str(stats.correct_answers)),
        ("Incorrect answers", str(stats.total_questions - stats.correct_answers)),
        ("Accuracy", _accuracy_text(stats)),
        ("Distinct cards missed", str(len(stats.missed_terms))),
    ]
    return _format_table(rows) + _missed_terms_lines(stats.missed_terms)


def run(
    argv: Sequence[str] | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    error_fn: Callable[[str], None] = _print_error,
) -> int:
    """Run the quiz from the command line.

    After the closing line, a short summary is shown, or the full report if
    ``--stats`` was given. Nothing is shown if the deck cannot be loaded.

    Args:
        argv: Command line arguments. ``sys.argv[1:]`` is used if ``None``.
        input_fn: Function used to read an answer.
        output_fn: Function used to show a message.
        error_fn: Function used to report an error.

    Returns:
        0 when the quiz ends or the user quits, 1 when the deck cannot be
        loaded.
    """
    args = build_parser().parse_args(argv)
    try:
        cards = load_flashcards(args.file)
        session = QuizSession(QuizModeFactory.create_mode(args.mode, cards))
    except (FlashcardLoadError, ValueError) as error:
        error_fn(f"Error: {error}")
        return EXIT_LOAD_ERROR
    finished = _ask_questions(session, input_fn, output_fn)
    output_fn("Quiz finished." if finished else "Quiz stopped.")
    output_fn("")
    stats = session.stats()
    if args.stats:
        lines = _report_lines(stats, args.mode, args.file, len(cards), finished)
    else:
        lines = _summary_lines(stats)
    for line in lines:
        output_fn(line)
    return EXIT_OK
