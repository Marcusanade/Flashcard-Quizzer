"""Unit tests for ``utils.file_handler.read_text_file``."""

from pathlib import Path

import pytest

from utils.file_handler import read_text_file

BOM = b"\xef\xbb\xbf"


def write_bytes(directory: Path, content: bytes, name: str = "file.txt") -> Path:
    """Write raw ``content`` bytes to ``directory/name`` and return the path."""
    path = directory / name
    path.write_bytes(content)
    return path


def test_read_text_file_returns_content(tmp_path: Path) -> None:
    path = write_bytes(tmp_path, b"hello\nworld")

    text = read_text_file(path)

    assert text == "hello\nworld"


@pytest.mark.parametrize("as_string", [True, False], ids=["str", "path"])
def test_read_text_file_accepts_str_and_path(tmp_path: Path, as_string: bool) -> None:
    path = write_bytes(tmp_path, b"hello")
    argument = str(path) if as_string else path

    text = read_text_file(argument)

    assert text == "hello"


def test_read_text_file_discards_leading_bom(tmp_path: Path) -> None:
    path = write_bytes(tmp_path, BOM + b"hello")

    text = read_text_file(path)

    assert not text.startswith("\ufeff")
    assert text == "hello"


def test_read_text_file_same_text_with_and_without_bom(tmp_path: Path) -> None:
    with_bom = write_bytes(tmp_path, BOM + b"hello", name="with_bom.txt")
    without_bom = write_bytes(tmp_path, b"hello", name="without_bom.txt")

    text_with = read_text_file(with_bom)
    text_without = read_text_file(without_bom)

    assert text_with == text_without


def test_read_text_file_reads_non_ascii_text(tmp_path: Path) -> None:
    path = write_bytes(tmp_path, "ñ é ü".encode("utf-8"))

    text = read_text_file(path)

    assert text == "ñ é ü"


def test_read_text_file_empty_file_returns_empty_string(tmp_path: Path) -> None:
    path = write_bytes(tmp_path, b"")

    text = read_text_file(path)

    assert text == ""


def test_read_text_file_directory_raises_is_a_directory_error(
    tmp_path: Path,
) -> None:
    with pytest.raises(IsADirectoryError) as info:
        read_text_file(tmp_path)

    assert str(tmp_path) in str(info.value)


def test_read_text_file_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    path = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        read_text_file(path)


def test_read_text_file_invalid_utf8_raises_unicode_decode_error(
    tmp_path: Path,
) -> None:
    path = write_bytes(tmp_path, b"\xff\xfe\x00")

    with pytest.raises(UnicodeDecodeError):
        read_text_file(path)
