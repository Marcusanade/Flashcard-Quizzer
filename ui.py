"""Console interface for the Flashcard Quizzer.

This module reads the command line arguments, loads the deck, runs the quiz
loop and prints the messages. The quiz logic lives in ``quiz_engine`` and the
deck loading in ``data_loader``: this module only talks to the user.
"""

import argparse
import sys
from collections.abc import Callable, Sequence

from data_loader import FlashcardLoadError, load_flashcards
from models import Flashcard
from quiz_engine import AnswerResult, QuizModeFactory, QuizSession

EXIT_OK = 0
EXIT_LOAD_ERROR = 1


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


def _feedback_line(result: AnswerResult) -> str:
    """Build the feedback shown after an answer.

    Args:
        result: The outcome of the answer.

    Returns:
        ``Correct!`` or ``Incorrect. Answer: <expected>``.
    """
    if result.correct:
        return "Correct!"
    return f"Incorrect. Answer: {result.expected}"


def _ask_questions(
    session: QuizSession,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> None:
    """Ask questions until the session has no more cards.

    Args:
        session: The quiz session.
        input_fn: Function used to read an answer.
        output_fn: Function used to show a message.
    """
    # Two identical cards in a deck are equal, so for the "(review)" label
    # they count as the same card.
    asked: set[Flashcard] = set()
    number = 0
    while (card := session.next_question()) is not None:
        number += 1
        output_fn(_question_line(number, card, card in asked))
        asked.add(card)
        result = session.submit_answer(input_fn("> "))
        output_fn(_feedback_line(result))


def run(
    argv: Sequence[str] | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    error_fn: Callable[[str], None] = _print_error,
) -> int:
    """Run the quiz from the command line.

    Args:
        argv: Command line arguments. ``sys.argv[1:]`` is used if ``None``.
        input_fn: Function used to read an answer.
        output_fn: Function used to show a message.
        error_fn: Function used to report an error.

    Returns:
        0 when the quiz ends normally, 1 when the deck cannot be loaded.
    """
    args = build_parser().parse_args(argv)
    try:
        cards = load_flashcards(args.file)
        session = QuizSession(QuizModeFactory.create_mode(args.mode, cards))
    except (FlashcardLoadError, ValueError) as error:
        error_fn(f"Error: {error}")
        return EXIT_LOAD_ERROR
    _ask_questions(session, input_fn, output_fn)
    output_fn("Quiz finished.")
    return EXIT_OK
