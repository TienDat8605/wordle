# Wordle Game

Python implementation of Wordle featuring an interactive GUI, AI solvers with **configurable cost and heuristic functions**, visual animations, and comprehensive benchmarking utilities.

## Features
- Classic Wordle gameplay with a Tkinter GUI and comprehensive 14,855-word dictionary
- Direct cell input with keyboard navigation (type, backspace across cells, Enter to submit)
- **26 AI solver configurations**: BFS, DFS, UCS (4 cost functions), A* (4 cost × 5 heuristic = 20 variants)
- **Configurable search strategies**: Choose different cost functions (constant, candidate reduction, partition balance, entropy) and heuristics (ratio, remaining, log2, entropy gap, partition)
- Search-based AI solvers with on-screen animation of their decision process
- Benchmark harness measuring solver latency, memory usage (via `tracemalloc`), and node expansion counts
- **Sparse feedback table caching**: Optimized memory usage with max 100 connections per word (~1.5M pairs instead of 221M)
- Extensible code structure for experimenting with additional heuristics or word lists

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
- First run automatically builds sparse feedback cache (~2-5 seconds for 14,855 words)
- Uses sparse graph optimization: max 100 connections per word to prevent OOM
- Subsequent runs load from cache instantly (<100ms)
- Cache stored in `.cache/` directory (~113 MB)

## Usage

### Playing the Game
1. **Manual Play**: Type letters directly into the grid cells
   - Letters auto-advance to next cell
   - Backspace deletes current cell or moves back
   - Press Enter to submit when row is complete
   
2. **AI Solver**: Select a solver (BFS/DFS/UCS/A*) and click **Run Solver** to watch it solve
   - Animated step-by-step solution (750ms per guess)
   - Shows the solver's decision-making process
   
3. **Benchmark**: Click **Benchmark** to test all solvers
   - Configure number of samples and random seed
   - View performance metrics in the results panel

### Running Benchmarks via CLI
```bash
# Run with custom parameters
python run_benchmarks.py --samples 10 --seed 42

# Default: 5 samples, seed 7
python run_benchmarks.py
```

## Solvers

### Core Algorithms
- **BFS** – Breadth-first search: explores states level by level, guarantees minimum guesses
- **DFS** – Depth-first search: memory efficient, explores deeply before backtracking  
- **UCS** – Uniform cost search with **4 configurable cost functions**
- **A*** – A* search with **4 cost functions × 5 heuristic functions = 20 variants**

### Cost Functions (UCS and A*)
Cost functions determine **g(n)** – the accumulated cost to reach state n. Lower cost = better guess path.

| Function | Mathematical Formula | Description | Use Case |
|----------|---------------------|-------------|----------|
| **constant** | $c(s) = 1$ | Every guess costs the same | Baseline (UCS = BFS) |
| **reduction** | $c(s) = 1 + \frac{\|C_{after}\|}{\|C_{before}\|}$ | Rewards candidate elimination | ⭐ **RECOMMENDED** |
| **partition** | $c(s) = 1 + \frac{\max(\|P_i\|)}{\|C_{before}\|}$ | Penalizes large partitions | Avoids worst-case |
| **entropy** | $c(s) = 2 - \frac{H(X)}{H_{max}}$ | High entropy = cheap | Information theory |

Where:
- $\|C_{before}\|$ = number of candidates before guess
- $\|C_{after}\|$ = number of candidates after guess  
- $P_i$ = partition i of candidates (grouped by feedback pattern)
- $H(X) = -\sum p_i \log_2(p_i)$ = Shannon entropy of partitions
- $H_{max} = \log_2(\|C_{before}\|)$ = maximum possible entropy

### Heuristic Functions (A* only)
Heuristics estimate **h(n)** – the remaining cost to reach the goal. Used in A* priority: $f(n) = g(n) + h(n)$

| Function | Mathematical Formula | Admissible? | Description |
|----------|---------------------|-------------|-------------|
| **ratio** | $h(n) = \frac{\|C_{remaining}\|}{5}$ | ❌ | Simple division by word length |
| **remaining** | $h(n) = \|C_{remaining}\|$ | ❌ | Direct candidate count |
| **log2** | $h(n) = \log_2(\|C_{remaining}\|)$ | ✅ | Minimum binary splits needed ⭐ |
| **entropy** | $h(n) = H_{max} - H(X)$ | ❌ | Information gap to certainty |
| **partition** | $h(n) = \log_2(\max(\|P_i\|))$ | ✅ | Worst-case partition size |

**Admissibility**: A heuristic is admissible if $h(n) \leq h^*(n)$ (never overestimates true cost). Admissible heuristics guarantee optimal solutions in A*.

*See REPORT.md for detailed mathematical derivations and performance comparisons.*

## Benchmark Results *(samples=10, seed=42)*

### Default Solvers (constant cost, ratio heuristic)

| Solver | Success | Avg Time (ms) | Max Time (ms) | Avg Memory (KB) | Max Memory (KB) | Avg Nodes |
|--------|---------|---------------|---------------|-----------------|-----------------|-----------|
| **BFS** | 100% | 2258.27 | 18927.55 | 185240.96 | 1828805.23 | 124.3 |
| **DFS** | 100% | 61.38 | 65.36 | 597.49 | 802.07 | 5.3 |
| **UCS-constant** | 100% | 415.42 | 1676.13 | 2871.36 | 8204.15 | 124.3 |
| **A*-constant-ratio** | 100% | 57.56 | 59.71 | 597.49 | 802.07 | 4.0 |

### Recommended Configurations (single word test)

Test on "WORLD":

| Solver | Guesses | Nodes Explored | Improvement |
|--------|---------|----------------|-------------|
| `bfs-opt` | 2 | 247 | Baseline |
| `ucs-reduction` | 2 | 73 | 70% fewer nodes |
| `astar-constant-log2` | 2 | 3 | **99% fewer nodes!** |
| `astar-reduction-log2` | 2 | 3 | **99% fewer nodes!** |

**Key Findings:**
- A* is 39× faster than BFS with 310× less memory usage
- **log2 heuristic** is dramatically more efficient (247 → 3 nodes)
- **reduction cost** improves search by 70%
- All solvers achieve 100% success rate within 6 guesses
- DFS is surprisingly effective due to constraint propagation

Run `python run_benchmarks.py --samples 10 --seed 42` to regenerate these metrics.

## Project Structure

```
Wordle/
├── wordle/               # Main package
│   ├── game.py           # Core game logic
│   ├── gui.py            # Tkinter UI
│   ├── solver_optimized.py  # Search algorithms (26 configs)
│   ├── feedback.py       # Feedback evaluation
│   ├── feedback_table.py # Sparse feedback cache (max 100 connections/word)
│   ├── knowledge.py      # Constraint tracking
│   ├── words.py          # 14,855-word dataset loader
│   └── benchmark.py      # Performance testing
├── valid_solutions.csv   # 14,855 five-letter words
├── run_game.py           # Game launcher
├── run_cache.py          # Precompute feedback cache
├── run_benchmarks.py     # CLI benchmarking
├── build_executable.sh   # Linux/Mac build script
├── build_executable.bat  # Windows build script
├── README.md             # This file
└── REPORT.md             # Detailed analysis
```

## Technical Highlights

- **26 Solver Configurations**: Combine 4 cost functions with 5 heuristics for experimentation
- **Sparse Feedback Table**: ~1.5M pairs cached (99.3% memory reduction vs full table)
  - Max 100 random connections per word (sparse graph optimization)
  - Prevents OOM on 14,855-word dataset (would be 221M pairs otherwise)
  - Fallback to on-the-fly computation for cache misses
- **Efficient State Representation**: Immutable frozen dataclass for O(1) hashing
- **Constraint Propagation**: Incremental filtering reduces search space
- **Branching Limiting**: Max 30 candidates per state prevents blowup

For detailed algorithm analysis, cost/heuristic explanations, and implementation details, see **REPORT.md**.

See `REPORT.md` for detailed algorithm analysis and implementation notes.