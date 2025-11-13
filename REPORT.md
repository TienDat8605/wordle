# Wordle AI Project Report

## Overview
This project delivers a Python-based Wordle experience that combines a playable GUI with four classical search solvers (BFS, DFS, UCS, A*). The implementation emphasises clear separation between game state, solver logic, and presentation, enabling benchmarking and visualisation of solver behaviour.

## Architecture
- **Core game** (`wordle/game.py`): Maintains the canonical game state, validates guesses, and produces feedback compatible with the official rules.
- **Knowledge model** (`wordle/knowledge.py`): Tracks positional and frequency constraints extracted from feedback, allowing solvers to prune infeasible candidates efficiently.
- **Dictionary loader** (`wordle/words.py` + `valid_solutions.csv`): Loads the full NYT-style solution set supplied via CSV, falling back to a compact curated list if the dataset is absent.
- **Solvers** (`wordle/solver.py`): Implements graph-search abstractions with interchangeable frontier strategies (queue, stack, priority queue, heuristic ordering). Search nodes include immutable history and cloned knowledge to prevent cross-branch contamination.
- **GUI** (`wordle/gui.py`): Uses Tkinter widgets (labels, buttons, option menus) as documented in the [Tkinter Docs project](https://context7.com/rdbende/tkinter-docs) to render the board, capture user input, and animate solver output.
- **Benchmarking** (`wordle/benchmark.py`): Executes each solver against sampled answers while recording wall-clock time, peak memory via `tracemalloc`, and search effort metrics.

## GUI Highlights
- 6×5 grid of `tk.Label` widgets mirroring the familiar Wordle layout with colour-coded feedback.
- Entry field and buttons to manage human gameplay, restart sessions, and launch solver animations.
- Animation loop scheduled with `after(...)`, replaying solver-derived guesses at 750 ms intervals.

## Solver Strategies
- **BFS**: Level-order exploration of knowledge-consistent candidate subsets.
- **DFS**: Depth-first backtracking prioritising deeper speculative branches.
- **UCS**: Uniform cost search treating each guess as unit cost; offers the same optimality guarantees as BFS under equal action costs.
- **A***: Augments uniform cost with a heuristic (candidate pool size) to favour states that dramatically shrink the remaining search space.

Each solver shares a common search scaffold but customises frontier ordering and priority calculation, facilitating comparative analysis while minimising duplicated logic.

## Benchmark Results *(samples=5, seed=7)*
| Solver | Success | Avg time (ms) | Max time (ms) | Avg peak KiB | Max peak KiB | Avg nodes |
| --- | --- | --- | --- | --- | --- | --- |
| BFS | 100% | 3.98 | 6.47 | 103.42 | 148.60 | 7.8 |
| DFS | 100% | 2.18 | 2.52 | 50.86 | 54.08 | 4.8 |
| UCS | 100% | 3.21 | 4.22 | 98.93 | 131.04 | 7.8 |
| ASTAR | 100% | 1.83 | 2.00 | 46.08 | 50.22 | 5.4 |

*Observations*
- All solvers succeed within the six-guess limit on the sampled set, thanks to the curated dictionary and aggressive constraint propagation.
- DFS offers a speed advantage on this dataset because consistent candidate sets are small, reducing backtracking cost.
- A* achieves the best overall latency and memory profile by prioritising states that shrink the candidate pool.

## Future Enhancements
- Import a larger dictionary (e.g., NYT Wordle list) and incorporate entropy-based heuristics for more realistic difficulty.
- Add persistence for benchmark runs and combine with plotting utilities for visual comparison.
- Explore web deployment via `pyodide` or `Flask` to satisfy the optional hosting requirement.
