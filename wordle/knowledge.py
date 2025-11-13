"""Stateful representation of accumulated Wordle knowledge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from .feedback import Feedback, Mark


@dataclass
class WordleKnowledge:
    """Captures constraints discovered from previous guesses."""

    word_length: int = 5
    known_positions: Dict[int, str] = field(default_factory=dict)
    excluded_positions: Dict[int, Set[str]] = field(default_factory=dict)
    min_counts: Dict[str, int] = field(default_factory=dict)
    max_counts: Dict[str, int] = field(default_factory=dict)
    excluded_letters: Set[str] = field(default_factory=set)

    def incorporate(self, guess: str, feedback: Feedback) -> None:
        """Update constraints using feedback from a guess."""

        guess = guess.lower()
        positives: Dict[str, int] = {}

        for idx, (letter, mark) in enumerate(zip(guess, feedback)):
            if mark is Mark.CORRECT:
                self.known_positions[idx] = letter
                positives[letter] = positives.get(letter, 0) + 1
            elif mark is Mark.PRESENT:
                self.excluded_positions.setdefault(idx, set()).add(letter)
                positives[letter] = positives.get(letter, 0) + 1
            else:
                self.excluded_positions.setdefault(idx, set()).add(letter)

        # Update min/max counts per letter.
        letter_counts: Dict[str, int] = {}
        for letter in guess:
            letter_counts[letter] = letter_counts.get(letter, 0) + 1

        for letter, total in letter_counts.items():
            positive_count = positives.get(letter, 0)
            if positive_count == 0:
                self.excluded_letters.add(letter)
                self.max_counts[letter] = 0
                continue
            self.min_counts[letter] = max(self.min_counts.get(letter, 0), positive_count)
            current_max = self.max_counts.get(letter)
            if current_max is None:
                self.max_counts[letter] = positive_count
            else:
                self.max_counts[letter] = min(current_max, positive_count)

    def candidate_filter(self, words: List[str]) -> List[str]:
        """Return a list of words consistent with accumulated constraints."""

        return [word for word in words if self.is_word_possible(word)]

    def is_word_possible(self, word: str) -> bool:
        """Check whether a word satisfies the current knowledge constraints."""

        if len(word) != self.word_length:
            return False

        word = word.lower()

        for idx, letter in self.known_positions.items():
            if word[idx] != letter:
                return False

        for idx, letter in enumerate(word):
            if letter in self.excluded_letters:
                return False
            if letter in self.excluded_positions.get(idx, set()) and idx not in self.known_positions:
                return False

        counts: Dict[str, int] = {}
        for letter in word:
            counts[letter] = counts.get(letter, 0) + 1

        for letter, minimum in self.min_counts.items():
            if counts.get(letter, 0) < minimum:
                return False

        for letter, maximum in self.max_counts.items():
            if maximum == 0 and counts.get(letter, 0) > 0:
                return False
            if counts.get(letter, 0) > maximum:
                return False

        return True

    def clone(self) -> "WordleKnowledge":
        """Create a deep copy suitable for branching search."""

        return WordleKnowledge(
            word_length=self.word_length,
            known_positions=dict(self.known_positions),
            excluded_positions={idx: set(letters) for idx, letters in self.excluded_positions.items()},
            min_counts=dict(self.min_counts),
            max_counts=dict(self.max_counts),
            excluded_letters=set(self.excluded_letters),
        )

    def signature(self) -> tuple:
        """Return a hashable signature to detect repeated search states."""

        known = tuple(sorted(self.known_positions.items()))
        excluded = tuple(
            (idx, tuple(sorted(letters))) for idx, letters in sorted(self.excluded_positions.items())
        )
        mins = tuple(sorted(self.min_counts.items()))
        maxs = tuple(sorted(self.max_counts.items()))
        excludes = tuple(sorted(self.excluded_letters))
        return (known, excluded, mins, maxs, excludes)
