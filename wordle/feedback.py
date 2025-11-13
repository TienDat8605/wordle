"""Feedback utilities for evaluating Wordle guesses."""

from __future__ import annotations

from enum import Enum, auto
from typing import Iterable, List


class Mark(Enum):
    """Represents the feedback for a single letter in a Wordle guess."""

    MISS = auto()
    PRESENT = auto()
    CORRECT = auto()

    def to_color(self) -> str:
        """Return a Tkinter-friendly color string for the mark."""

        if self is Mark.CORRECT:
            return "#6aaa64"  # green
        if self is Mark.PRESENT:
            return "#c9b458"  # yellow
        return "#787c7e"  # gray

    def to_symbol(self) -> str:
        """Return a human-readable symbol for the mark."""

        if self is Mark.CORRECT:
            return "G"
        if self is Mark.PRESENT:
            return "Y"
        return "-"


Feedback = List[Mark]


def evaluate_guess(answer: str, guess: str) -> Feedback:
    """Compute Wordle-style feedback for a guess given the answer."""

    answer = answer.lower()
    guess = guess.lower()
    feedback: Feedback = [Mark.MISS] * len(guess)
    answer_char_counts: dict[str, int] = {}

    for char in answer:
        answer_char_counts[char] = answer_char_counts.get(char, 0) + 1

    # First pass: mark correct positions.
    for idx, (g_char, a_char) in enumerate(zip(guess, answer)):
        if g_char == a_char:
            feedback[idx] = Mark.CORRECT
            answer_char_counts[g_char] -= 1

    # Second pass: mark present letters.
    for idx, g_char in enumerate(guess):
        if feedback[idx] is Mark.CORRECT:
            continue
        if answer_char_counts.get(g_char, 0) > 0:
            feedback[idx] = Mark.PRESENT
            answer_char_counts[g_char] -= 1

    return feedback


def feedback_to_string(feedback: Iterable[Mark]) -> str:
    """Convert a feedback sequence to a compact string representation."""

    return "".join(mark.to_symbol() for mark in feedback)
