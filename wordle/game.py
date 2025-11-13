"""Game loop and state management for Wordle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

from .feedback import Feedback, evaluate_guess
from .knowledge import WordleKnowledge
from .words import WORD_LIST, random_answer


@dataclass
class GameState:
    """Represents the observable state of an ongoing game."""

    history: List[Tuple[str, Feedback]] = field(default_factory=list)
    max_attempts: int = 6
    answer: str = ""

    @property
    def is_won(self) -> bool:
        """Return whether the player has guessed the answer."""

        return bool(self.history and self.history[-1][0] == self.answer)

    @property
    def is_lost(self) -> bool:
        """Return whether the player has exhausted all attempts."""

        return not self.is_won and len(self.history) >= self.max_attempts

    @property
    def remaining_attempts(self) -> int:
        """Return the number of guesses still available."""

        return self.max_attempts - len(self.history)


class WordleGame:
    """Encapsulates Wordle game logic and state progression."""

    def __init__(
        self,
        word_list: Sequence[str] | None = None,
        max_attempts: int = 6,
        answer: str | None = None,
    ) -> None:
        self.word_list = list(word_list or WORD_LIST)
        self.max_attempts = max_attempts
        self.answer = (answer or random_answer()).lower()
        self.knowledge = WordleKnowledge(word_length=len(self.answer))
        self.state = GameState(max_attempts=max_attempts, answer=self.answer)

    def reset(self, answer: str | None = None) -> None:
        """Reset the game with a new random answer or provided answer."""

        self.answer = (answer or random_answer()).lower()
        self.knowledge = WordleKnowledge(word_length=len(self.answer))
        self.state = GameState(max_attempts=self.max_attempts, answer=self.answer)

    def valid_guess(self, guess: str) -> bool:
        """Return whether the guess is in the curated word list."""

        return guess.lower() in self.word_list

    def apply_guess(self, guess: str) -> Feedback:
        """Apply a guess, update state, and return feedback."""

        guess = guess.lower()
        if not self.valid_guess(guess):
            raise ValueError(f"Invalid guess: {guess}")
        if self.state.is_won or self.state.is_lost:
            raise RuntimeError("Game already finished")

        feedback = evaluate_guess(self.answer, guess)
        self.knowledge.incorporate(guess, feedback)
        self.state.history.append((guess, feedback))
        return feedback

    def current_state(self) -> GameState:
        """Return the current game state snapshot."""

        return self.state
