"""Utility module containing the playable word list."""

from __future__ import annotations

import csv
import random
from functools import lru_cache
from pathlib import Path
from typing import Iterable

_PACKAGE_DIR = Path(__file__).resolve().parent
_CANDIDATE_PATHS: tuple[Path, ...] = (
    _PACKAGE_DIR / "valid_solutions.csv",
    _PACKAGE_DIR.parent / "valid_solutions.csv",
)

# Compact fallback set ensures the game remains playable if the dataset is missing.
_FALLBACK_WORDS: tuple[str, ...] = (
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
)


def _resolve_data_path(path: str | Path | None) -> Path | None:
    """Resolve the preferred CSV path, probing fallback locations."""

    if path is not None:
        csv_path = Path(path)
        if csv_path.exists():
            return csv_path

    for candidate in _CANDIDATE_PATHS:
        if candidate.exists():
            return candidate

    return None


def _iter_word_rows(csv_path: Path) -> Iterable[str]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row:
                continue
            entry = row[0].strip().lower()
            if entry == "word":
                # Skip header row if present.
                continue
            if len(entry) == 5 and entry.isalpha():
                yield entry


@lru_cache
def load_word_list(path: str | Path | None = None) -> list[str]:
    """Load the curated word list from CSV, normalising to lowercase."""

    csv_path = _resolve_data_path(path)
    if csv_path is None:
        return list(_FALLBACK_WORDS)

    words = list(_iter_word_rows(csv_path))

    return words or list(_FALLBACK_WORDS)


# Load once at import for convenient module-level access.
WORD_LIST: list[str] = load_word_list()


def random_answer(rng: random.Random | None = None) -> str:
    """Return a random answer from the curated list."""

    generator = rng or random
    return generator.choice(WORD_LIST)
