"""Utility module containing the playable word list."""

from __future__ import annotations

import csv
import random
from pathlib import Path

# Load the comprehensive word list from valid_solutions.csv
_CSV_PATH = Path(__file__).parent.parent / "valid_solutions.csv"


def _load_word_list() -> list[str]:
    """Load five-letter words from the CSV dataset."""
    words: list[str] = []
    with open(_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row["word"].strip().lower()
            if len(word) == 5:
                words.append(word)
    return words


WORD_LIST: list[str] = _load_word_list()


def random_answer(rng: random.Random | None = None) -> str:
    """Return a random answer from the curated list."""

    generator = rng or random
    return generator.choice(WORD_LIST)
