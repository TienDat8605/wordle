"""Optimized feedback lookup table for performance."""

from __future__ import annotations

import hashlib
import pickle
import random
from pathlib import Path
from typing import Dict, Sequence, Tuple

from .feedback import Feedback, evaluate_guess


class FeedbackTable:
    """Precomputed feedback lookup for sparse (guess, target) pairs.
    
    Uses a sparse graph structure where each word connects to at most
    max_connections other words to avoid OOM on large datasets.
    """

    def __init__(self, word_list: Sequence[str], max_connections: int = 100) -> None:
        """Build or load the sparse feedback table for the given word list.
        
        Args:
            word_list: List of valid words
            max_connections: Maximum number of connections per word (default 100)
                           to create a sparse graph and avoid memory issues.
        
        The table is cached to disk and only rebuilt if the word list changes.
        """
        self._table: Dict[Tuple[str, str], Feedback] = {}
        self._max_connections = max_connections
        
        # Generate a hash of the word list to detect changes
        word_list_sorted = sorted(w.lower() for w in word_list)
        word_hash = hashlib.md5("".join(word_list_sorted).encode()).hexdigest()[:8]
        
        # Cache file path (include max_connections to distinguish sparse tables)
        cache_dir = Path(__file__).parent.parent / ".cache"
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f"feedback_table_{len(word_list)}_{word_hash}_sparse{max_connections}.pkl"
        
        # Try loading from cache
        if cache_file.exists():
            print(f"Loading feedback table from cache...", flush=True)
            try:
                with open(cache_file, "rb") as f:
                    self._table = pickle.load(f)
                print(f"  [OK] Loaded {len(self._table)} entries from cache")
                return
            except Exception as e:
                print(f"  [WARNING] Cache load failed: {e}, rebuilding...")
        
        # Build the sparse table
        print(f"Building sparse feedback table for {len(word_list)} words...", flush=True)
        print(f"  Using sparse graph: max {max_connections} connections per word", flush=True)
        
        # Use deterministic random sampling for reproducibility
        rng = random.Random(42)
        
        for i, guess in enumerate(word_list):
            if (i + 1) % 500 == 0:
                print(f"  Progress: {i + 1}/{len(word_list)}", end="\r", flush=True)
            
            # Always include self-connection (guess == target)
            key_self = (guess.lower(), guess.lower())
            self._table[key_self] = evaluate_guess(guess, guess)
            
            # Sample up to (max_connections - 1) other random words
            others = [w for w in word_list if w != guess]
            sample_size = min(max_connections - 1, len(others))
            if sample_size > 0:
                targets = rng.sample(others, sample_size)
                
                for target in targets:
                    key = (guess.lower(), target.lower())
                    self._table[key] = evaluate_guess(target, guess)
        
        print(f"  [OK] Sparse feedback table built: {len(self._table)} entries" + " " * 20)
        
        # Save to cache
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(self._table, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"  [OK] Saved to cache: {cache_file.name}")
        except Exception as e:
            print(f"  [WARNING] Cache save failed: {e}")

    def get_feedback(self, guess: str, target: str) -> Feedback:
        """Retrieve feedback, using cache or computing on-the-fly.
        
        Args:
            guess: The guessed word
            target: The target/answer word
            
        Returns:
            Feedback tuple indicating correctness of each letter
        """
        key = (guess.lower(), target.lower())
        
        # Return cached feedback if available
        if key in self._table:
            return self._table[key]
        
        # Fallback: compute on-the-fly for sparse graph cache misses
        return evaluate_guess(target, guess)
