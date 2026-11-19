"""Console interface for the Flashcard Quizzer.

This module reads the command line arguments, loads the deck, runs the quiz
loop and prints the messages. The quiz logic lives in ``quiz_engine`` and the
deck loading in ``data_loader``: this module only talks to the user.
"""

import argparse
import sys
import textwrap
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from data_loader import FlashcardLoadError, load_flashcards
from models import Flashcard
from quiz_engine import AnswerResult, QuizModeFactory, QuizSession, SessionStats
from sound import SilentPlayer, SoundPlayer, create_player

EXIT_OK = 0
EXIT_LOAD_ERROR = 1

REPORT_WIDTH = 60
BAR_CELLS = 20
LABEL_WIDTH = 19
REPORT_TITLE = "SESSION REPORT"
TEXT_WIDTH = REPORT_WIDTH - 4
VALUE_WIDTH = TEXT_WIDTH - LABEL_WIDTH

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


def _positive_int(text: str) -> int:
    """Convert a command line text to an integer greater than zero.

    Args:
        text: The text typed by the user.

    Returns:
        The integer.

    Raises:
        argparse.ArgumentTypeError: If the text is not an integer or is less
            than 1.
    """
    try:
        value = int(text)
    except ValueError:
        value = 0
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be a positive integer: {text!r}")
    return value


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
        "--limit",
        type=_positive_int,
        default=None,
        metavar="N",
        help="stop after N answered questions (repeated questions count)",
    )
    parser.add_argument(
        "--sound",
        action="store_true",
        help=(
            "ring the terminal bell after each answer "
            "(one ring if correct, three if incorrect)"
        ),
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


def _play_result(player: SoundPlayer, result: AnswerResult) -> None:
    """Play the sound that matches the result of an answer.

    Args:
        player: The sound player.
        result: The outcome of the answer.
    """
    if result.correct:
        player.play_success()
    else:
        player.play_failure()


def _ask_questions(
    session: QuizSession,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
    sound: SoundPlayer | None = None,
) -> bool:
    """Ask questions until the session has no more cards or the user quits.

    A question that was shown but not answered is not counted. If the user
    quits with Ctrl+C or by closing the input, an empty line is shown first
    so the next message starts on a new line. The sound of an answer is played
    right after its feedback line. Nothing is played when the user quits.

    Args:
        session: The quiz session.
        input_fn: Function used to read an answer.
        output_fn: Function used to show a message.
        sound: Player of the sounds. A silent player is used if it is
            ``None``.

    Returns:
        True if the session ran out of cards, False if the user quit.
    """
    # Two identical cards in a deck are equal, so for the "(review)" label
    # they count as the same card.
    player = sound if sound is not None else SilentPlayer()
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
        result = session.submit_answer(reply.answer)
        output_fn(_feedback_line(result))
        _play_result(player, result)
    return True


def _border(fill: str) -> str:
    """Build a horizontal border of the report box.

    Args:
        fill: The character that fills the border, ``=`` or ``-``.

    Returns:
        A line of ``REPORT_WIDTH`` characters.
    """
    return "+" + fill * (REPORT_WIDTH - 2) + "+"


def _row(text: str) -> str:
    """Build one row of the report box.

    Args:
        text: The text of the row, at most ``TEXT_WIDTH`` characters.

    Returns:
        The text left-justified between the side bars.
    """
    return "| " + text.ljust(TEXT_WIDTH) + " |"


def _title_row(title: str) -> str:
    """Build the row that shows the title, centered.

    Args:
        title: The title text.

    Returns:
        The row with the centered title.
    """
    return _row(title.center(TEXT_WIDTH))


def _fit(text: str, width: int) -> str:
    """Shorten a text that does not fit, keeping its end.

    The end is kept because the end of a path is the useful part.

    Args:
        text: The text to fit.
        width: The maximum number of characters.

    Returns:
        The same text if it fits, otherwise ``...`` followed by the last
        ``width - 3`` characters.
    """
    if len(text) <= width:
        return text
    return "..." + text[len(text) - (width - 3) :]


def _pair_row(label: str, value: str) -> str:
    """Build a ``label / value`` row.

    Args:
        label: The label, shown in a column of ``LABEL_WIDTH`` characters.
        value: The value, shortened if it is longer than ``VALUE_WIDTH``.

    Returns:
        The row.
    """
    return _row(label.ljust(LABEL_WIDTH) + _fit(value, VALUE_WIDTH))


def _accuracy_bar(correct: int, total: int) -> str:
    """Build the accuracy bar with integer arithmetic only.

    Args:
        correct: Number of correct answers.
        total: Number of questions.

    Returns:
        ``BAR_CELLS`` cells between square brackets, ``#`` for the filled
        ones. The filled cells are ``20 * correct / total`` rounded half up,
        and none if there are no questions.
    """
    filled = 0
    if total > 0:
        filled = (40 * correct + total) // (2 * total)
    return "[" + "#" * filled + "-" * (BAR_CELLS - filled) + "]"


def _rank(correct: int, total: int) -> str:
    """Compute the rank letter with integer arithmetic only.

    Args:
        correct: Number of correct answers.
        total: Number of questions.

    Returns:
        ``-`` with no questions, otherwise S (all correct), A (at least 90%),
        B (at least 75%), C (at least 60%) or D.
    """
    if total == 0:
        return "-"
    if correct == total:
        return "S"
    if 10 * correct >= 9 * total:
        return "A"
    if 4 * correct >= 3 * total:
        return "B"
    if 5 * correct >= 3 * total:
        return "C"
    return "D"


def _accuracy_text(stats: SessionStats) -> str:
    """Format the accuracy with one decimal.

    Args:
        stats: The session statistics.

    Returns:
        For example ``66.7%``.
    """
    return f"{stats.accuracy_percent:.1f}%"


def _accuracy_cell(stats: SessionStats) -> str:
    """Build the value of the accuracy row: the bar and the percentage.

    Args:
        stats: The session statistics.

    Returns:
        The bar, a space and the accuracy text right-aligned in 6 characters.
    """
    bar = _accuracy_bar(stats.correct_answers, stats.total_questions)
    return bar + " " + _accuracy_text(stats).rjust(6)


def _missed_rows(missed: Sequence[str]) -> list[str]:
    """Build the rows that list the missed terms.

    Args:
        missed: The missed terms, in order of first miss.

    Returns:
        One row ``Missed terms: none`` if there are none, otherwise a title
        row followed by the wrapped terms. The first line of each term starts
        with ``  - `` and the following lines with four spaces.
    """
    if not missed:
        return [_row("Missed terms: none")]
    rows = [_row("Missed terms")]
    for term in missed:
        parts = textwrap.wrap(term, width=TEXT_WIDTH - 4, break_long_words=True)
        for index, part in enumerate(parts):
            prefix = "  - " if index == 0 else "    "
            rows.append(_row(prefix + part))
    return rows


def _head_lines() -> list[str]:
    """Build the top border, the title row and the border below it.

    Returns:
        The three lines.
    """
    return [_border("="), _title_row(REPORT_TITLE), _border("=")]


def _summary_lines(stats: SessionStats) -> list[str]:
    """Build the short summary shown at the end of the quiz.

    Args:
        stats: The session statistics.

    Returns:
        The complete box, missed terms included.
    """
    return [
        *_head_lines(),
        _pair_row("Total questions", str(stats.total_questions)),
        _pair_row("Accuracy", _accuracy_cell(stats)),
        _pair_row("Rank", _rank(stats.correct_answers, stats.total_questions)),
        _border("-"),
        *_missed_rows(stats.missed_terms),
        _border("="),
    ]


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
        The complete box, missed terms included.
    """
    incorrect = stats.total_questions - stats.correct_answers
    return [
        *_head_lines(),
        _pair_row("Mode", mode),
        _pair_row("Deck file", deck_file),
        _pair_row("Deck size", str(deck_size)),
        _pair_row("Session", "finished" if finished else "stopped"),
        _border("-"),
        _pair_row("Total questions", str(stats.total_questions)),
        _pair_row("Correct answers", str(stats.correct_answers)),
        _pair_row("Incorrect answers", str(incorrect)),
        _pair_row("Accuracy", _accuracy_cell(stats)),
        _pair_row("Rank", _rank(stats.correct_answers, stats.total_questions)),
        _border("-"),
        *_missed_rows(stats.missed_terms),
        _border("="),
    ]


def run(
    argv: Sequence[str] | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    error_fn: Callable[[str], None] = _print_error,
    sound: SoundPlayer | None = None,
) -> int:
    """Run the quiz from the command line.

    After the closing line, a short summary is shown, or the full report if
    ``--stats`` was given. Nothing is shown if the deck cannot be loaded.

    Args:
        argv: Command line arguments. ``sys.argv[1:]`` is used if ``None``.
        input_fn: Function used to read an answer.
        output_fn: Function used to show a message.
        error_fn: Function used to report an error.
        sound: Player of the sounds. If it is given it is used, whatever
            ``--sound`` says. If it is ``None``, the player is created from
            the ``--sound`` flag.

    Returns:
        0 when the quiz ends or the user quits, 1 when the deck cannot be
        loaded.
    """
    args = build_parser().parse_args(argv)
    try:
        cards = load_flashcards(args.file)
        mode = QuizModeFactory.create_mode(args.mode, cards)
        session = QuizSession(mode, max_questions=args.limit)
    except (FlashcardLoadError, ValueError) as error:
        error_fn(f"Error: {error}")
        return EXIT_LOAD_ERROR
    player = sound if sound is not None else create_player(args.sound)
    finished = _ask_questions(session, input_fn, output_fn, player)
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
