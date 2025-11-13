"""Utility module containing the playable word list."""

from __future__ import annotations

import random

# Curated set of five-letter words to keep solver branching manageable.
WORD_LIST: list[str] = [
    "cigar",
    "rebut",
    "sissy",
    "humph",
    "awake",
    "blush",
    "focal",
    "evade",
    "naval",
    "serve",
    "heath",
    "dwarf",
    "model",
    "grade",
    "quiet",
    "bench",
    "feign",
    "major",
    "death",
    "fresh",
]


def random_answer(rng: random.Random | None = None) -> str:
    """Return a random answer from the curated list."""

    generator = rng or random
    return generator.choice(WORD_LIST)
