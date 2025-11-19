#!/usr/bin/env python3
"""Precompute the feedback table cache before running the game.

This script builds the sparse feedback table (max 100 connections per word)
and saves it to .cache/ for fast game startup.
"""

from wordle.feedback_table import FeedbackTable
from wordle.words import WORD_LIST


def main():
    """Build and cache the feedback table."""
    print("=" * 60)
    print("Wordle Feedback Table Cache Builder")
    print("=" * 60)
    print(f"Word list size: {len(WORD_LIST)} words")
    print(f"Sparse graph: max 100 connections per word")
    print(f"Expected cache size: ~{len(WORD_LIST) * 100 / 1_000_000:.1f}M entries")
    print("=" * 60)
    print()
    
    # Build the feedback table (will cache automatically)
    FeedbackTable(WORD_LIST, max_connections=100)
    
    print()
    print("=" * 60)
    print("[OK] Cache build complete!")
    print("You can now run: python -m wordle")
    print("=" * 60)


if __name__ == "__main__":
    main()
