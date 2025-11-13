"""Optimized feedback lookup table for performance."""

from __future__ import annotations

from typing import Dict, Sequence, Tuple

from .feedback import Feedback, evaluate_guess


class FeedbackTable:
    """Precomputed feedback lookup for all (guess, target) pairs."""

    def __init__(self, word_list: Sequence[str]) -> None:
        """Build the feedback table for the given word list.
        
        This is expensive but only done once per solver initialization.
        """
        self._table: Dict[Tuple[str, str], Feedback] = {}
        print(f"Building feedback table for {len(word_list)} words...", flush=True)
        
        for i, guess in enumerate(word_list):
            if (i + 1) % 500 == 0:
                print(f"  Progress: {i + 1}/{len(word_list)}", end="\r", flush=True)
            for target in word_list:
                key = (guess.lower(), target.lower())
                self._table[key] = evaluate_guess(target, guess)
        
        print(f"  Feedback table built: {len(self._table)} entries" + " " * 20)

    def get_feedback(self, guess: str, target: str) -> Feedback:
        """Retrieve precomputed feedback."""
        return self._table[(guess.lower(), target.lower())]
