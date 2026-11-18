"""Load and validate flashcard decks stored as JSON files.

Two JSON layouts are accepted:

* Array format: ``[{"front": "...", "back": "..."}, ...]``
* Object format: ``{"cards": [{"front": "...", "back": "..."}, ...]}``

This module only raises exceptions. It does not print and it knows nothing
about the quiz or the command line.
"""

import json
from pathlib import Path
from typing import Any

from models import Flashcard
from utils.file_handler import read_text_file

CARDS_KEY = "cards"
FRONT_KEY = "front"
BACK_KEY = "back"


class FlashcardLoadError(Exception):
    """Raised when a flashcard deck cannot be read or is not valid.

    The message is always a single readable line with no internal details.
    The original exception, when there is one, is kept as ``__cause__``.
    """


def load_flashcards(path: str | Path) -> list[Flashcard]:
    """Load a flashcard deck from a JSON file.

    Both the array format and the ``{"cards": [...]}`` object format are
    supported. Validation stops at the first problem found. Texts are
    stripped of surrounding whitespace and extra keys in a card are ignored.

    Args:
        path: Location of the JSON file, as a string or a ``pathlib.Path``.

    Returns:
        The cards of the deck, in file order.

    Raises:
        FlashcardLoadError: If the path is empty, the file cannot be read,
            the JSON is malformed, or the deck structure or any card is
            invalid.
    """
    if isinstance(path, str) and not path.strip():
        raise FlashcardLoadError("The file path is empty.")
    text = _read_deck_text(path)
    data = _parse_json(text, path)
    raw_cards = _extract_cards(data)
    return [_build_card(raw, position) for position, raw in enumerate(raw_cards, 1)]


def _read_deck_text(path: str | Path) -> str:
    """Read the deck file and translate read errors into load errors.

    Args:
        path: Location of the JSON file.

    Returns:
        The text of the file.

    Raises:
        FlashcardLoadError: If the file cannot be read for any reason.
    """
    try:
        return read_text_file(path)
    except FileNotFoundError as error:
        raise FlashcardLoadError(f'File not found: "{path}".') from error
    except IsADirectoryError as error:
        raise FlashcardLoadError(
            f'Path is a directory, not a file: "{path}".'
        ) from error
    except PermissionError as error:
        raise FlashcardLoadError(
            f'No permission to read the file: "{path}".'
        ) from error
    except UnicodeDecodeError as error:
        raise FlashcardLoadError(f'File is not valid UTF-8 text: "{path}".') from error
    except OSError as error:
        raise FlashcardLoadError(f'Could not read the file: "{path}".') from error


def _parse_json(text: str, path: str | Path) -> Any:
    """Parse JSON text.

    Args:
        text: The JSON document.
        path: Location of the file, used only in the error message.

    Returns:
        The parsed JSON value.

    Raises:
        FlashcardLoadError: If the text is not valid JSON. The message
            includes the line and column of the error.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise FlashcardLoadError(
            f'Invalid JSON in "{path}": {error.msg} '
            f"(line {error.lineno}, column {error.colno})."
        ) from error


def _extract_cards(data: object) -> list[Any]:
    """Get the list of raw cards from the parsed JSON root.

    Args:
        data: The parsed JSON root.

    Returns:
        The non-empty list of raw cards.

    Raises:
        FlashcardLoadError: If the root has an unsupported shape, the
            ``cards`` value is not a list, or the list is empty.
    """
    if isinstance(data, dict) and CARDS_KEY in data:
        data = data[CARDS_KEY]
        if not isinstance(data, list):
            raise FlashcardLoadError(f'The "{CARDS_KEY}" value must be a list.')
    if not isinstance(data, list):
        raise FlashcardLoadError(
            f'The deck must be a list of cards or an object with a "{CARDS_KEY}" key.'
        )
    cards: list[Any] = data
    if not cards:
        raise FlashcardLoadError("The deck has no cards.")
    return cards


def _build_card(raw: object, position: int) -> Flashcard:
    """Validate one raw card and build a Flashcard from it.

    Args:
        raw: The raw JSON value for the card.
        position: Position of the card in the deck, counting from 1.

    Returns:
        The validated card with stripped texts.

    Raises:
        FlashcardLoadError: If the card is not an object or a field is
            missing, not a string, or blank.
    """
    if not isinstance(raw, dict):
        raise FlashcardLoadError(f"Card {position} is not a JSON object.")
    front = _read_field(raw, FRONT_KEY, position)
    back = _read_field(raw, BACK_KEY, position)
    return Flashcard(front=front, back=back)


def _read_field(card: dict[str, Any], name: str, position: int) -> str:
    """Read and validate one text field of a card.

    Args:
        card: The raw card object.
        name: Name of the field to read.
        position: Position of the card in the deck, counting from 1.

    Returns:
        The field value with surrounding whitespace removed.

    Raises:
        FlashcardLoadError: If the field is missing, is not a string, or is
            empty or only whitespace.
    """
    if name not in card:
        raise FlashcardLoadError(f'Card {position} is missing the "{name}" field.')
    value = card[name]
    if not isinstance(value, str):
        raise FlashcardLoadError(f'Card {position} has a non-string "{name}" field.')
    text = value.strip()
    if not text:
        raise FlashcardLoadError(f'Card {position} has an empty "{name}" field.')
    return text
