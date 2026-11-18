"""Low-level file reading helpers."""

from pathlib import Path


def read_text_file(path: str | Path) -> str:
    """Read a whole text file as UTF-8, tolerating a leading BOM.

    The encoding is explicit so the behavior is identical on Windows and
    Linux. A directory is rejected up front because opening one raises
    PermissionError on Windows but IsADirectoryError elsewhere.

    Args:
        path: Location of the file, as a string or a ``pathlib.Path``.

    Returns:
        The full contents of the file.

    Raises:
        IsADirectoryError: If ``path`` points to a directory.
        FileNotFoundError: If ``path`` does not exist.
        PermissionError: If the file cannot be read due to permissions.
        UnicodeDecodeError: If the file is not valid UTF-8.
    """
    file_path = Path(path)
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
    with open(file_path, encoding="utf-8-sig") as file:
        return file.read()
