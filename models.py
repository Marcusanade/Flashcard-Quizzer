"""Data models for the Flashcard Quizzer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Flashcard:
    """A single flashcard with a question side and an answer side.

    Instances are immutable. This class holds data only: validation
    belongs to the data loader.

    Attributes:
        front: The prompt shown to the user.
        back: The expected answer.
    """

    front: str
    back: str
