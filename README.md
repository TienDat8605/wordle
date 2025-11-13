# Wordle Game

Python implementation of Wordle featuring an interactive GUI, AI solvers (BFS, DFS, UCS, A*), visual animations, and benchmarking utilities.

## Features
- Classic Wordle gameplay with a Tkinter GUI and curated five-letter dictionary.
- Search-based AI solvers (BFS, DFS, UCS, A*) with on-screen animation of their decision process.
- Benchmark harness measuring solver latency, memory usage (via `tracemalloc`), and node expansion counts.
- Extensible code structure for experimenting with additional heuristics or word lists.

## Getting Started
1. (Optional) create a virtual environment:
	 ```bash
	 python -m venv .venv
	 source .venv/bin/activate
	 ```
2. Install dependencies (standard library only; no extra packages required).

## Usage
- Launch the GUI:
	```bash
	python -m wordle
	```
- Run solver benchmarks:
	```bash
	python -m wordle.benchmark
	```
- Animate a solver from the GUI by selecting it in the dropdown and clicking **Run Solver**.

## Solvers
- **BFS** – breadth-first exploration of consistent candidate spaces.
- **DFS** – depth-first search with backtracking over candidate constraints.
- **UCS** – uniform cost search where each guess has equal cost.
- **A\*** – A* search prioritising smaller candidate pools.

## Benchmark Snapshot *(samples=5, seed=7)*

| Solver | Success | Avg time (ms) | Max time (ms) | Avg peak KiB | Max peak KiB | Avg nodes |
| --- | --- | --- | --- | --- | --- | --- |
| BFS | 100% | 3.98 | 6.47 | 103.42 | 148.60 | 7.8 |
| DFS | 100% | 2.18 | 2.52 | 50.86 | 54.08 | 4.8 |
| UCS | 100% | 3.21 | 4.22 | 98.93 | 131.04 | 7.8 |
| ASTAR | 100% | 1.83 | 2.00 | 46.08 | 50.22 | 5.4 |

Re-run `python -m wordle.benchmark` to regenerate metrics or adjust sampling.

## Project Structure

- `wordle/game.py` – core game state and validation.
- `wordle/gui.py` – Tkinter user interface and solver animation.
- `wordle/solver.py` – search implementations and registry.
- `wordle/benchmark.py` – benchmarking utilities and CLI entry point.
- `wordle/words.py` – curated five-letter word list.

See `REPORT.md` for implementation notes and solver analysis.