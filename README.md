# Wordle Game

Python implementation of Wordle featuring an interactive GUI, AI solvers (BFS, DFS, UCS, A*), visual animations, and benchmarking utilities.

## Features
- Classic Wordle gameplay with a Tkinter GUI and curated 2,315-word dictionary
- Direct cell input with keyboard navigation (type, backspace across cells, Enter to submit)
- Search-based AI solvers (BFS, DFS, UCS, A*) with on-screen animation of their decision process
- Benchmark harness measuring solver latency, memory usage (via `tracemalloc`), and node expansion counts
- Persistent feedback table caching for instant startup (precomputed 5.3M feedback pairs)
- Extensible code structure for experimenting with additional heuristics or word lists

## Quick Start

### Option 1: Run from Source
Requirements: Python 3.8+ (standard library only, no external dependencies)

```bash
# Clone or download the repository
git clone https://github.com/TienDat8605/wordle.git
cd wordle

# Run the game (cache will be built automatically on first run)
python -m wordle

# Or use the launcher script
python run_game.py
```

**Note**: First run will take 2-5 seconds to build the feedback cache (5.3M precomputed pairs). Subsequent runs will be instant (<100ms).

### Option 2: Run as Executable
Build a standalone executable with the precomputed cache included:

```bash
# Install PyInstaller (one-time setup)
pip install pyinstaller

# Build the executable
./build_executable.sh

# Run the game
./dist/WordleAI          # Linux/Mac
dist\WordleAI.exe        # Windows
```

The executable includes:
- Complete game with GUI
- All 4 AI solvers
- Precomputed feedback cache (no build delay)
- 2,315-word dataset
- Benchmark functionality

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
- **BFS** – Breadth-first search: explores states level by level, guarantees minimum guesses
- **DFS** – Depth-first search: memory efficient, explores deeply before backtracking  
- **UCS** – Uniform cost search: treats each guess as unit cost, equivalent to BFS for Wordle
- **A*** – A* search with admissible heuristic (candidate pool size): fastest solver, maintains optimality

## Benchmark Results *(samples=10, seed=42)*

| Solver | Success | Avg Time (ms) | Max Time (ms) | Avg Memory (KB) | Max Memory (KB) | Avg Nodes |
|--------|---------|---------------|---------------|-----------------|-----------------|-----------|
| **BFS** | 100% | 2258.27 | 18927.55 | 185240.96 | 1828805.23 | 124.3 |
| **DFS** | 100% | 61.38 | 65.36 | 597.49 | 802.07 | 5.3 |
| **UCS** | 100% | 415.42 | 1676.13 | 2871.36 | 8204.15 | 124.3 |
| **A*** | 100% | 57.56 | 59.71 | 597.49 | 802.07 | 4.0 |

**Key Findings:**
- A* is 39× faster than BFS with 310× less memory usage
- All solvers achieve 100% success rate within 6 guesses
- DFS is surprisingly effective due to constraint propagation
- BFS has exponential memory growth issues at scale

Run `python run_benchmarks.py --samples 10 --seed 42` to regenerate these metrics.

## Project Structure

```
Wordle/
├── wordle/
│   ├── game.py              # Core game state and validation
│   ├── gui.py               # Tkinter UI with keyboard input
│   ├── solver_optimized.py  # Optimized search implementations
│   ├── feedback.py          # Feedback evaluation (Mark enum)
│   ├── feedback_table.py    # Precomputed feedback cache
│   ├── knowledge.py         # Constraint tracking system
│   ├── words.py             # 2,315-word dataset loader
│   └── benchmark.py         # Performance measurement utilities
├── valid_solutions.csv      # Curated word list
├── run_game.py              # Game launcher script
├── run_benchmarks.py        # Benchmark CLI tool
├── build_executable.sh      # Executable build script
└── REPORT.md                # Detailed implementation report
```

## Technical Highlights

- **Precomputed Feedback Table**: 5,359,225 feedback pairs cached to disk
  - First run: ~2-5 seconds to build
  - Subsequent runs: <100ms to load from cache
  
- **Efficient State Representation**: Frozen dataclass with immutable history for O(1) hashing

- **Constraint Propagation**: WordleKnowledge class incrementally updates constraints
  - Known positions, excluded positions
  - Min/max letter counts
  - Excluded letters
  
- **Branching Factor Limiting**: Max 30 candidates per state prevents exponential blowup

## Performance Notes

On a typical system:
- **Game launch**: Instant (cache loads in <100ms)
- **A* solver**: ~58ms average per puzzle
- **GUI response**: Immediate, smooth animations
- **Memory usage**: ~600KB for DFS/A*, ~185MB for BFS

See `REPORT.md` for detailed algorithm analysis and implementation notes.