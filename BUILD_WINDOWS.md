# Building Wordle Executable for Windows

## Prerequisites

1. **Python 3.8 or higher** installed on Windows
   - Download from: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **PyInstaller** (will be installed automatically by the script)

## Quick Build (Automated)

### Option 1: Using the Batch Script (Easiest)

1. Open the project folder in File Explorer
2. Double-click `build_executable.bat`
3. Wait for the build to complete (may take 1-2 minutes)
4. Find the executable at: `dist\WordleAI.exe`

### Option 2: Using Command Prompt

1. Open Command Prompt (Win + R, type `cmd`, press Enter)
2. Navigate to project folder:
   ```cmd
   cd path\to\Wordle
   ```

3. Run the build script:
   ```cmd
   build_executable.bat
   ```

4. The executable will be created at: `dist\WordleAI.exe`

## Manual Build (Advanced)

If you prefer to build manually:

```cmd
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --noconfirm --name "WordleAI" --onefile --windowed --add-data "valid_solutions.csv;." --add-data ".cache;cache" --hidden-import tkinter --hidden-import tkinter.messagebox --collect-all wordle run_game.py
```

## Running the Executable

After building:

1. Navigate to the `dist` folder
2. Double-click `WordleAI.exe`
3. The game window should open

## Distributing the Executable

The `WordleAI.exe` file in the `dist` folder is **completely standalone**. You can:

- Copy it to any Windows computer (no Python required)
- Share it with others
- Run it from a USB drive
- No installation needed - just double-click to play!

The executable includes:
- ✓ Complete game with GUI
- ✓ All 4 AI solvers (BFS, DFS, UCS, A*)
- ✓ Precomputed feedback cache (instant startup)
- ✓ 2,315-word dataset
- ✓ Benchmark functionality

## File Size

The executable will be approximately **15-20 MB** including:
- Python interpreter
- Tkinter GUI library
- All game code and data
- Precomputed cache

## Troubleshooting

### "Python is not recognized"
- Reinstall Python and check "Add Python to PATH"
- Or manually add Python to your PATH environment variable

### "PyInstaller not found"
- Run: `pip install pyinstaller`
- Or let the build script install it automatically

### Build fails with permission error
- Run Command Prompt as Administrator
- Or check antivirus isn't blocking PyInstaller

### Executable doesn't run
- Make sure you're running `WordleAI.exe` from the `dist` folder
- Check Windows Defender didn't quarantine the file
- Some antivirus software may flag PyInstaller executables (false positive)

### "Failed to execute script"
- Make sure `.cache` folder and `valid_solutions.csv` are bundled
- Rebuild using the provided script

## Advanced Options

### Build without console window
The script already uses `--windowed` flag (no console window)

### Build with console for debugging
Remove `--windowed` from the PyInstaller command:
```cmd
pyinstaller --noconfirm --name "WordleAI" --onefile --add-data "valid_solutions.csv;." --add-data ".cache;cache" --hidden-import tkinter --hidden-import tkinter.messagebox --collect-all wordle run_game.py
```

### Custom icon
Add an icon file:
```cmd
pyinstaller ... --icon=icon.ico run_game.py
```

## Build Time

- First build: **1-2 minutes**
- Subsequent builds: **30-60 seconds**
- Feedback cache generation: **2-5 seconds** (first time only)

## Testing the Executable

After building, test all features:
1. ✓ Game launches successfully
2. ✓ Can type letters and submit guesses
3. ✓ All 4 solvers work (BFS, DFS, UCS, A*)
4. ✓ Benchmark function works
5. ✓ New Game button resets properly
6. ✓ Window resizes correctly

## Distribution Checklist

When sharing the executable:
- ✓ Test on a clean Windows machine (without Python installed)
- ✓ Include this README if needed
- ✓ Compress with 7-Zip or WinRAR to reduce download size
- ✓ Consider code signing to avoid Windows SmartScreen warnings (optional)
