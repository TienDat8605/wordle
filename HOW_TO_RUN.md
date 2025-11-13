# How to Run the Wordle Game

## Quick Start (Recommended)

The simplest way to run the game:

```bash
python run_game.py
```

Or:

```bash
python -m wordle
```

## Building an Executable

To create a standalone executable that includes everything (game, solvers, cache):

```bash
# 1. Install PyInstaller (one-time setup)
pip install pyinstaller

# 2. Run the build script
./build_executable.sh

# 3. Run the executable
./dist/WordleAI          # Linux/Mac
dist\WordleAI.exe        # Windows
```

The executable will be located in the `dist/` folder and includes:
- Complete game with GUI
- All 4 AI solvers (BFS, DFS, UCS, A*)
- Precomputed feedback cache (instant startup)
- 2,315-word dataset

## What's Included

✅ **GUI Features:**
- Direct cell input (type letters directly into grid)
- Auto-advance to next cell
- Backspace across entire row
- Enter key to submit guess
- White background with large 36pt font
- Color-coded feedback (green/yellow/gray)

✅ **AI Solvers:**
- BFS - Breadth-first search
- DFS - Depth-first search  
- UCS - Uniform cost search
- A* - A* with candidate pool heuristic

✅ **Benchmark Tool:**
- Click "Benchmark" button in GUI
- Configure samples and seed
- View performance results

## System Requirements

- Python 3.8 or higher
- Standard library only (no external dependencies for running the game)
- PyInstaller required only for building executable

## Troubleshooting

**Issue**: Game takes 2-5 seconds to start first time  
**Solution**: This is normal - building feedback cache. Subsequent runs will be instant (<100ms).

**Issue**: Executable build fails  
**Solution**: Make sure PyInstaller is installed: `pip install pyinstaller`

**Issue**: Can't run build_executable.sh  
**Solution**: Make it executable: `chmod +x build_executable.sh`
