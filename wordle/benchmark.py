"""Benchmark helpers for Wordle solvers."""

from __future__ import annotations

import statistics
import time
import tracemalloc
from dataclasses import dataclass
from random import Random
from typing import Dict, Iterable, List

from .solver_optimized import OPTIMIZED_SOLVERS, SolverResult
from .words import WORD_LIST


# Default solvers for benchmarking (basic 4 algorithms)
DEFAULT_BENCHMARK_SOLVERS = ['bfs-opt', 'dfs-opt', 'ucs-constant', 'astar-constant-log2']


@dataclass
class BenchmarkStats:
    """Aggregate statistics for a solver across multiple runs."""

    solver: str
    runs: int
    success_rate: float
    avg_time_ms: float
    max_time_ms: float
    avg_peak_kib: float
    max_peak_kib: float
    avg_nodes_expanded: float


def _benchmark_solver(solver_name: str, answers: Iterable[str], 
                      candidates_per_answer: Dict[str, List[str]]) -> BenchmarkStats:
    solver = OPTIMIZED_SOLVERS[solver_name]
    elapsed_times: List[float] = []
    peak_memories: List[int] = []
    successes = 0
    nodes_expanded: List[int] = []

    answers_list = list(answers)
    for idx, answer in enumerate(answers_list, 1):
        print(f"  {solver_name.upper()}: {idx}/{len(answers_list)} - {answer}", end="\r", flush=True)
        tracemalloc.start()
        start = time.perf_counter()
        starting_cands = candidates_per_answer[answer]
        result: SolverResult = solver.solve(answer, WORD_LIST, starting_candidates=starting_cands)
        elapsed = (time.perf_counter() - start) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        elapsed_times.append(elapsed)
        peak_memories.append(peak)
        nodes_expanded.append(result.expanded_nodes)
        if result.success:
            successes += 1

    print(" " * 80, end="\r")  # Clear progress line
    runs = len(elapsed_times)
    success_rate = successes / runs if runs else 0.0
    avg_time = statistics.fmean(elapsed_times) if runs else 0.0
    max_time = max(elapsed_times, default=0.0)
    avg_peak = statistics.fmean(peak_memories) / 1024 if runs else 0.0
    max_peak = (max(peak_memories) / 1024) if runs else 0.0
    avg_nodes = statistics.fmean(nodes_expanded) if runs else 0.0

    return BenchmarkStats(
        solver=solver_name,
        runs=runs,
        success_rate=success_rate,
        avg_time_ms=avg_time,
        max_time_ms=max_time,
        avg_peak_kib=avg_peak,
        max_peak_kib=max_peak,
        avg_nodes_expanded=avg_nodes,
    )


def run_benchmarks(samples: int = 3, seed: int = 7, solvers: List[str] | None = None) -> Dict[str, BenchmarkStats]:
    """Run solvers on a subset of answers and return aggregated stats.
    
    Args:
        samples: Number of random words to test.
        seed: Random seed for reproducibility.
        solvers: List of solver names to benchmark. If None, uses default 4 basic solvers.
    """

    rng = Random(seed)
    answers = [rng.choice(WORD_LIST) for _ in range(samples)]
    print(f"Benchmarking on {samples} random words: {', '.join(answers)}\n")
    
    # Generate random starting candidates once per answer (all solvers use same candidates)
    candidates_per_answer: Dict[str, List[str]] = {}
    for answer in answers:
        candidates_per_answer[answer] = rng.sample(WORD_LIST, 30)
    
    # Use provided solvers or default to basic 4
    solver_list = solvers if solvers is not None else DEFAULT_BENCHMARK_SOLVERS
    
    stats: Dict[str, BenchmarkStats] = {}
    for solver_name in solver_list:
        if solver_name not in OPTIMIZED_SOLVERS:
            print(f"Warning: Solver '{solver_name}' not found, skipping...")
            continue
        stats[solver_name] = _benchmark_solver(solver_name, answers, candidates_per_answer)
    return stats


def print_benchmarks(samples: int = 3, seed: int = 7) -> None:
    """Execute benchmarks and print a summary table."""

    stats = run_benchmarks(samples=samples, seed=seed)
    headers = (
        "Solver",
        "Success",
        "Avg time (ms)",
        "Max time (ms)",
        "Avg peak KiB",
        "Max peak KiB",
        "Avg nodes",
    )
    print(" | ".join(headers))
    print("-" * 80)
    for solver_name, stat in stats.items():
        row = (
            solver_name.upper(),
            f"{stat.success_rate * 100:.0f}%",
            f"{stat.avg_time_ms:.2f}",
            f"{stat.max_time_ms:.2f}",
            f"{stat.avg_peak_kib:.2f}",
            f"{stat.max_peak_kib:.2f}",
            f"{stat.avg_nodes_expanded:.1f}",
        )
        print(" | ".join(row))
