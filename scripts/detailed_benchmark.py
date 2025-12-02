"""Detailed benchmark collector: records avg guesses per solver/run.

Runs the same sampling used by `run_benchmarks.py` but collects
per-run guess counts in addition to time, memory and node stats.
"""

from __future__ import annotations

import statistics
import time
import tracemalloc
from random import Random
from typing import Dict, List

from wordle.solver_optimized import OPTIMIZED_SOLVERS
from wordle.words import WORD_LIST


def detailed_benchmark(samples: int = 10, seed: int = 36, solvers: List[str] | None = None):
    rng = Random(seed)
    answers = [rng.choice(WORD_LIST) for _ in range(samples)]
    print(f"Detailed benchmarking on {samples} random words: {', '.join(answers)}\n")

    candidates_per_answer: Dict[str, List[str]] = {}
    for answer in answers:
        candidates_per_answer[answer] = rng.sample(WORD_LIST, 30)

    solver_list = solvers if solvers is not None else ['bfs-opt', 'dfs-opt', 'ucs-constant', 'astar-constant-log2']

    results = {}
    for solver_name in solver_list:
        if solver_name not in OPTIMIZED_SOLVERS:
            print(f"Warning: Solver '{solver_name}' not found, skipping...")
            continue

        solver = OPTIMIZED_SOLVERS[solver_name]
        elapsed_times: List[float] = []
        peak_memories: List[int] = []
        nodes_expanded: List[int] = []
        guesses_counts: List[int] = []
        successes = 0

        for idx, answer in enumerate(answers, 1):
            print(f"  {solver_name.upper()}: {idx}/{len(answers)} - {answer}", end="\r", flush=True)
            tracemalloc.start()
            start = time.perf_counter()
            starting_cands = candidates_per_answer[answer]
            result = solver.solve(answer, WORD_LIST, starting_candidates=starting_cands)
            elapsed = (time.perf_counter() - start) * 1000
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            elapsed_times.append(elapsed)
            peak_memories.append(peak)
            nodes_expanded.append(result.expanded_nodes)
            guesses_counts.append(len(result.history) if result.history is not None else 0)
            if result.success:
                successes += 1

        runs = len(elapsed_times)
        results[solver_name] = {
            'runs': runs,
            'success_rate': successes / runs if runs else 0.0,
            'avg_time_ms': statistics.fmean(elapsed_times) if runs else 0.0,
            'max_time_ms': max(elapsed_times) if runs else 0.0,
            'avg_peak_kib': statistics.fmean(peak_memories) / 1024 if runs else 0.0,
            'max_peak_kib': (max(peak_memories) / 1024) if runs else 0.0,
            'avg_nodes_expanded': statistics.fmean(nodes_expanded) if runs else 0.0,
            'avg_guesses': statistics.fmean(guesses_counts) if runs else 0.0,
        }

    print(" " * 80, end="\r")
    # Print a summary table
    headers = (
        "Solver",
        "Success",
        "Avg time (ms)",
        "Max time (ms)",
        "Avg peak KiB",
        "Max peak KiB",
        "Avg nodes",
        "Avg guesses",
    )
    print(" | ".join(headers))
    print("-" * 100)
    for solver_name, stat in results.items():
        row = (
            solver_name.upper(),
            f"{stat['success_rate'] * 100:.0f}%",
            f"{stat['avg_time_ms']:.2f}",
            f"{stat['max_time_ms']:.2f}",
            f"{stat['avg_peak_kib']:.2f}",
            f"{stat['max_peak_kib']:.2f}",
            f"{stat['avg_nodes_expanded']:.1f}",
            f"{stat['avg_guesses']:.2f}",
        )
        print(" | ".join(row))


if __name__ == '__main__':
    detailed_benchmark()
