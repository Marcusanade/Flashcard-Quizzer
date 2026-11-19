"""Unit tests for ``data_loader.load_flashcards``.

Every test writes its own deck into pytest's ``tmp_path`` (or simulates a read
error with ``monkeypatch``), so no test depends on the working directory.
"""

import json
import re
from collections.abc import Callable
from pathlib import Path

import pytest

from data_loader import FlashcardLoadError, load_flashcards
from models import Flashcard

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BOM = b"\xef\xbb\xbf"


def write_deck(directory: Path, content: str, name: str = "deck.json") -> Path:
    """Write ``content`` as UTF-8 text to ``directory/name`` and return the path."""
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


def write_deck_bytes(directory: Path, content: bytes, name: str = "deck.json") -> Path:
    """Write raw ``content`` bytes to ``directory/name`` and return the path."""
    path = directory / name
    path.write_bytes(content)
    return path


def quoted(path: str | Path) -> str:
    """Return the regex-escaped, double-quoted form of ``path`` used in messages."""
    return '"' + re.escape(str(path)) + '"'


def assert_single_line(error: BaseException) -> None:
    """Assert that the error message fits on one line."""
    assert "\n" not in str(error)


def make_failing_reader(error: OSError) -> Callable[[str | Path], str]:
    """Build a replacement for ``read_text_file`` that always raises ``error``."""

    def fake_read(path: str | Path) -> str:
        """Raise the error given to the builder instead of reading."""
        raise error

    return fake_read


# --- Required course tests ---------------------------------------------------


def test_load_valid_flashcards_array(tmp_path: Path) -> None:
    path = write_deck(tmp_path, '[{"front": "A", "back": "B"}]')

    cards = load_flashcards(path)

    assert cards == [Flashcard(front="A", back="B")]


def test_load_valid_flashcards_object(tmp_path: Path) -> None:
    path = write_deck(tmp_path, '{"cards": [{"front": "A", "back": "B"}]}')

    cards = load_flashcards(path)

    assert cards == [Flashcard(front="A", back="B")]


def test_load_invalid_json(tmp_path: Path) -> None:
    path = write_deck(tmp_path, '[{"front": "A", "back": }]')

    with pytest.raises(FlashcardLoadError, match="Invalid JSON") as info:
        load_flashcards(path)

    assert_single_line(info.value)


def test_load_missing_required_field(tmp_path: Path) -> None:
    path = write_deck(tmp_path, '[{"front": "A"}]')

    with pytest.raises(
        FlashcardLoadError, match=re.escape('Card 1 is missing the "back" field.')
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


# --- Path and read errors ----------------------------------------------------


@pytest.mark.parametrize("value", ["", "   "], ids=["empty", "whitespace"])
def test_load_flashcards_empty_path(value: str) -> None:
    with pytest.raises(
        FlashcardLoadError, match=re.escape("The file path is empty.")
    ) as info:
        load_flashcards(value)

    assert_single_line(info.value)


def test_load_flashcards_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"

    with pytest.raises(
        FlashcardLoadError, match=f"File not found: {quoted(path)}"
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


def test_load_flashcards_path_is_directory(tmp_path: Path) -> None:
    with pytest.raises(
        FlashcardLoadError,
        match=f"Path is a directory, not a file: {quoted(tmp_path)}",
    ) as info:
        load_flashcards(tmp_path)

    assert_single_line(info.value)


def test_load_flashcards_permission_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_deck(tmp_path, '[{"front": "A", "back": "B"}]')
    # Patch the name inside data_loader: it did "from utils.file_handler import
    # read_text_file", so patching utils.file_handler would not affect it.
    monkeypatch.setattr(
        "data_loader.read_text_file", make_failing_reader(PermissionError("denied"))
    )

    with pytest.raises(
        FlashcardLoadError, match=f"No permission to read the file: {quoted(path)}"
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


def test_load_flashcards_generic_os_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_deck(tmp_path, '[{"front": "A", "back": "B"}]')
    # Same reason as above: patch the name where data_loader looks it up.
    monkeypatch.setattr(
        "data_loader.read_text_file", make_failing_reader(OSError("disk failure"))
    )

    with pytest.raises(
        FlashcardLoadError, match=f"Could not read the file: {quoted(path)}"
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


def test_load_flashcards_file_not_utf8(tmp_path: Path) -> None:
    path = write_deck_bytes(tmp_path, b"\xff\xfe\x00")

    with pytest.raises(
        FlashcardLoadError, match=f"File is not valid UTF-8 text: {quoted(path)}"
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


# --- JSON and structure errors -----------------------------------------------


def test_load_flashcards_malformed_json_reports_line_and_column(
    tmp_path: Path,
) -> None:
    path = write_deck(tmp_path, "[\n{bad}\n]")

    with pytest.raises(
        FlashcardLoadError,
        match=re.escape("(line 2, column 2).") + "$",
    ) as info:
        load_flashcards(path)

    assert str(info.value).startswith(f'Invalid JSON in "{path}": ')
    assert_single_line(info.value)


def test_load_flashcards_empty_file(tmp_path: Path) -> None:
    path = write_deck(tmp_path, "")

    with pytest.raises(
        FlashcardLoadError, match=re.escape("(line 1, column 1).")
    ) as info:
        load_flashcards(path)

    assert str(info.value).startswith("Invalid JSON in")
    assert_single_line(info.value)


@pytest.mark.parametrize(
    "content",
    ['"text"', "42", '{"deck": []}'],
    ids=["string", "number", "object-without-cards"],
)
def test_load_flashcards_unsupported_root(tmp_path: Path, content: str) -> None:
    path = write_deck(tmp_path, content)
    expected = 'The deck must be a list of cards or an object with a "cards" key.'

    with pytest.raises(FlashcardLoadError, match=re.escape(expected)) as info:
        load_flashcards(path)

    assert_single_line(info.value)


def test_load_flashcards_cards_value_not_a_list(tmp_path: Path) -> None:
    path = write_deck(tmp_path, '{"cards": "nope"}')

    with pytest.raises(
        FlashcardLoadError, match=re.escape('The "cards" value must be a list.')
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


@pytest.mark.parametrize(
    "content", ["[]", '{"cards": []}'], ids=["empty-array", "empty-cards"]
)
def test_load_flashcards_empty_deck(tmp_path: Path, content: str) -> None:
    path = write_deck(tmp_path, content)

    with pytest.raises(
        FlashcardLoadError, match=re.escape("The deck has no cards.")
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


@pytest.mark.parametrize(
    "card",
    ["5", '"text"', "null", '["front", "back"]'],
    ids=["number", "string", "null", "list"],
)
def test_load_flashcards_card_not_an_object(tmp_path: Path, card: str) -> None:
    path = write_deck(tmp_path, f"[{card}]")

    with pytest.raises(
        FlashcardLoadError, match=re.escape("Card 1 is not a JSON object.")
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


# --- Card field errors -------------------------------------------------------


def test_load_flashcards_missing_front(tmp_path: Path) -> None:
    path = write_deck(tmp_path, '[{"back": "B"}]')

    with pytest.raises(
        FlashcardLoadError, match=re.escape('Card 1 is missing the "front" field.')
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


@pytest.mark.parametrize("field", ["front", "back"])
@pytest.mark.parametrize(
    "value", [5, True, None, ["x"]], ids=["int", "bool", "null", "list"]
)
def test_load_flashcards_non_string_field(
    tmp_path: Path, field: str, value: object
) -> None:
    card = {"front": "A", "back": "B", field: value}
    path = write_deck(tmp_path, json.dumps([card]))

    with pytest.raises(
        FlashcardLoadError,
        match=re.escape(f'Card 1 has a non-string "{field}" field.'),
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


@pytest.mark.parametrize("field", ["front", "back"])
@pytest.mark.parametrize("value", ["", "   "], ids=["empty", "whitespace"])
def test_load_flashcards_blank_field(tmp_path: Path, field: str, value: str) -> None:
    card = {"front": "A", "back": "B", field: value}
    path = write_deck(tmp_path, json.dumps([card]))

    with pytest.raises(
        FlashcardLoadError,
        match=re.escape(f'Card 1 has an empty "{field}" field.'),
    ) as info:
        load_flashcards(path)

    assert_single_line(info.value)


# --- Behaviors ---------------------------------------------------------------


def test_load_flashcards_keeps_file_order(tmp_path: Path) -> None:
    content = json.dumps(
        [
            {"front": "third", "back": "3"},
            {"front": "first", "back": "1"},
            {"front": "second", "back": "2"},
        ]
    )
    path = write_deck(tmp_path, content)

    cards = load_flashcards(path)

    assert [card.front for card in cards] == ["third", "first", "second"]


def test_load_flashcards_strips_texts(tmp_path: Path) -> None:
    path = write_deck(tmp_path, '[{"front": " A ", "back": "\\tB\\n"}]')

    cards = load_flashcards(path)

    assert cards == [Flashcard(front="A", back="B")]


def test_load_flashcards_ignores_extra_keys(tmp_path: Path) -> None:
    path = write_deck(
        tmp_path, '[{"front": "A", "back": "B", "hint": "h", "level": 3}]'
    )

    cards = load_flashcards(path)

    assert cards == [Flashcard(front="A", back="B")]


def test_load_flashcards_position_counts_from_one(tmp_path: Path) -> None:
    content = json.dumps(
        [
            {"front": "A", "back": "B"},
            {"front": "C", "back": "D"},
            {"front": "E"},
        ]
    )
    path = write_deck(tmp_path, content)

    with pytest.raises(FlashcardLoadError, match="Card 3 "):
        load_flashcards(path)


def test_load_flashcards_stops_at_first_problem(tmp_path: Path) -> None:
    content = json.dumps([{"front": "A"}, {"back": "B"}])
    path = write_deck(tmp_path, content)

    with pytest.raises(FlashcardLoadError) as info:
        load_flashcards(path)

    assert str(info.value) == 'Card 1 is missing the "back" field.'


def test_load_flashcards_accepts_path_and_str(tmp_path: Path) -> None:
    path = write_deck(tmp_path, '[{"front": "A", "back": "B"}]')

    from_path = load_flashcards(path)
    from_str = load_flashcards(str(path))

    assert from_path == from_str == [Flashcard(front="A", back="B")]


def test_load_flashcards_deck_with_bom(tmp_path: Path) -> None:
    path = write_deck_bytes(tmp_path, BOM + b'[{"front": "A", "back": "B"}]')

    cards = load_flashcards(path)

    assert cards == [Flashcard(front="A", back="B")]


def test_load_flashcards_deck_without_bom(tmp_path: Path) -> None:
    path = write_deck_bytes(tmp_path, b'[{"front": "A", "back": "B"}]')

    cards = load_flashcards(path)

    assert cards == [Flashcard(front="A", back="B")]


# --- Exception chaining ------------------------------------------------------


def test_load_flashcards_missing_file_keeps_cause(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"

    with pytest.raises(FlashcardLoadError) as info:
        load_flashcards(path)

    assert isinstance(info.value.__cause__, FileNotFoundError)


def test_load_flashcards_invalid_json_keeps_cause(tmp_path: Path) -> None:
    path = write_deck(tmp_path, "{not json")

    with pytest.raises(FlashcardLoadError) as info:
        load_flashcards(path)

    assert isinstance(info.value.__cause__, json.JSONDecodeError)


# --- Real decks --------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "expected_count"),
    [("glossary.json", 10), ("python_basics.json", 8)],
)
def test_load_flashcards_real_decks(filename: str, expected_count: int) -> None:
    cards = load_flashcards(DATA_DIR / filename)

    assert len(cards) == expected_count
