# Wordle Game

Python implementation of Wordle featuring an interactive GUI, AI solvers with **configurable cost and heuristic functions**, visual animations, and comprehensive benchmarking utilities.

## Features
- **Classic Wordle Gameplay**: Interactive Tkinter GUI with a comprehensive 14,855-word dictionary.
- **Advanced AI Solvers**: 14 configurations including BFS, DFS, UCS, and A* with customizable cost and heuristic functions.
- **Optimized Performance**:
  - **Sparse Feedback Table**: Uses a sparse graph (max 200 connections/word) to cache feedback, reducing memory by ~98.6% (from 221M to ~3M entries) while maintaining O(1) lookup speed.
  - **Compact State Representation**: Efficient hashing and state tracking to minimize memory footprint during search.
  - **Branching Factor Control**: Limits search exploration to the most promising candidates to prevent combinatorial explosion.
- **Configurable Search Strategies**:
  - **Cost Functions**: Constant, Candidate Reduction, Partition Balance, Entropy.
  - **Heuristics**: Log2 (Admissible), Partition Size (Admissible).
- **Benchmarking Tool**: Measure solver latency, memory usage, and node expansion counts.

## Quick Start

### Run from Source
Requirements: Python 3.8+ (standard library only, no external dependencies)

```bash
# Clone the repository
git clone https://github.com/TienDat8605/wordle.git
cd wordle

# (Optional) Precompute feedback cache for faster first run
python run_cache.py

# Run the game
python -m wordle
# Or: python run_game.py
```

**Note**: 
- First run automatically builds sparse feedback cache (~2-5 seconds for 14,855 words).
- Uses sparse graph optimization: max 200 connections per word to prevent OOM.
- Subsequent runs load from cache instantly (<100ms).
- Cache stored in `.cache/` directory (~180 MB).

## Usage

### Playing the Game
1. **Manual Play**: Type letters directly into the grid cells.
   - Letters auto-advance to next cell.
   - Backspace deletes current cell or moves back.
   - Press Enter to submit when row is complete.
   
2. **AI Solver**: Select a solver (BFS/DFS/UCS/A*) and click **Run Solver** to watch it solve.
   - Animated step-by-step solution (750ms per guess).
   - Shows the solver's decision-making process.
   
3. **Benchmark**: Click **Benchmark** to test all solvers.
   - Configure number of samples and random seed.
   - View performance metrics in the results panel.

### Running Benchmarks via CLI
```bash
# Run with custom parameters
python run_benchmarks.py --samples 10 --seed 42

# Default: 5 samples, seed 7
python run_benchmarks.py
```

## Solvers

### Core Algorithms
- **BFS** – Breadth-first search: explores states level by level, guarantees minimum guesses.
- **DFS** – Depth-first search: memory efficient, explores deeply before backtracking.
- **UCS** – Uniform cost search with **4 configurable cost functions**.
- **A*** – A* search with **4 cost functions × 2 heuristic functions = 8 variants**.

### Cost Functions (UCS and A*)
Cost functions determine **g(n)** – the accumulated cost to reach state n. Lower cost = better guess path.

| Function | Mathematical Formula | Description | Use Case |
|----------|---------------------|-------------|----------|
| **constant** | $c(s) = 1$ | Every guess costs the same | Baseline (UCS = BFS) |
| **reduction** | $c(s) = 1 + \frac{\|C_{after}\|}{\|C_{before}\|}$ | Rewards candidate elimination | **RECOMMENDED** |

Where:
- $\|C_{before}\|$ = number of candidates before guess
- $\|C_{after}\|$ = number of candidates after guess  
- $P_i$ = partition i of candidates (grouped by feedback pattern)
- $H(X) = -\sum p_i \log_2(p_i)$ = Shannon entropy of partitions
- $H_{max} = \log_2(\|C_{before}\|)$ = maximum possible entropy

### Heuristic Functions (A* only)
Heuristics estimate **h(n)** – the remaining cost to reach the goal. Used in A* priority: $f(n) = g(n) + h(n)$

Only **admissible heuristics** are included to guarantee optimal solutions.

| Function | Mathematical Formula | Admissible? | Description |
|----------|---------------------|-------------|-------------|
| **log2** | $h(n) = \log_2(\|C_{remaining}\|)$ | Yes | Minimum binary splits needed. **RECOMMENDED** |

**Admissibility**: A heuristic is admissible if $h(n) \leq h^*(n)$ (never overestimates true cost). Admissible heuristics guarantee optimal solutions in A*.

## Technical Highlights

- **4 Solver Configurations**: Combine 2 cost functions with 1 admissible heuristic (plus BFS/DFS).
- **Sparse Feedback Table**: ~3M pairs cached (98.6% memory reduction vs full table).
  - Max 200 random connections per word (sparse graph optimization).
  - Prevents OOM on 14,855-word dataset.
  - Fallback to on-the-fly computation for cache misses.
- **Efficient State Representation**: Immutable frozen dataclass for O(1) hashing.
- **Constraint Propagation**: Incremental filtering reduces search space.
- **Branching Limiting**: Max 10 starting candidates per game prevents initial blowup.

For detailed algorithm analysis, cost/heuristic explanations, and implementation details, see **REPORT.md**.
