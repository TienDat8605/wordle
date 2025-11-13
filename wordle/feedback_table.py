"""Optimized feedback lookup table for performance."""

from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Dict, Sequence, Tuple

from .feedback import Feedback, evaluate_guess


class FeedbackTable:
    """Precomputed feedback lookup for all (guess, target) pairs."""

    def __init__(self, word_list: Sequence[str]) -> None:
        """Build or load the feedback table for the given word list.
        
        The table is cached to disk and only rebuilt if the word list changes.
        """
        self._table: Dict[Tuple[str, str], Feedback] = {}
        
        # Generate a hash of the word list to detect changes
        word_list_sorted = sorted(w.lower() for w in word_list)
        word_hash = hashlib.md5("".join(word_list_sorted).encode()).hexdigest()[:8]
        
        # Cache file path
        cache_dir = Path(__file__).parent.parent / ".cache"
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f"feedback_table_{len(word_list)}_{word_hash}.pkl"
        
        # Try loading from cache
        if cache_file.exists():
            print(f"Loading feedback table from cache...", flush=True)
            try:
                with open(cache_file, "rb") as f:
                    self._table = pickle.load(f)
                print(f"  ✓ Loaded {len(self._table)} entries from cache")
                return
            except Exception as e:
                print(f"  ⚠ Cache load failed: {e}, rebuilding...")
        
        # Build the table
        print(f"Building feedback table for {len(word_list)} words...", flush=True)
        
        for i, guess in enumerate(word_list):
            if (i + 1) % 500 == 0:
                print(f"  Progress: {i + 1}/{len(word_list)}", end="\r", flush=True)
            for target in word_list:
                key = (guess.lower(), target.lower())
                self._table[key] = evaluate_guess(target, guess)
        
        print(f"  ✓ Feedback table built: {len(self._table)} entries" + " " * 20)
        
        # Save to cache
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(self._table, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"  ✓ Saved to cache: {cache_file.name}")
        except Exception as e:
            print(f"  ⚠ Cache save failed: {e}")

    def get_feedback(self, guess: str, target: str) -> Feedback:
        """Retrieve precomputed feedback."""
        return self._table[(guess.lower(), target.lower())]
