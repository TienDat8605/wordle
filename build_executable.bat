@echo off
REM Build script for creating Wordle executable on Windows

echo Building Wordle Executable for Windows...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Create cache directory if it doesn't exist
if not exist ".cache" (
    echo Creating cache directory...
    mkdir .cache
)

REM Build feedback table cache if it doesn't exist
if not exist ".cache\feedback_table_2315_*.pkl" (
    echo Building feedback table cache (this may take a few seconds)...
    python -c "from wordle.feedback_table import FeedbackTable; from wordle.words import WORD_LIST; FeedbackTable.build_or_load(WORD_LIST)"
)

echo Building executable with PyInstaller...
pyinstaller --noconfirm ^
    --name "WordleAI" ^
    --onefile ^
    --windowed ^
    --add-data "valid_solutions.csv;." ^
    --add-data ".cache;cache" ^
    --hidden-import tkinter ^
    --hidden-import tkinter.messagebox ^
    --collect-all wordle ^
    run_game.py

echo.
echo Build complete!
echo.
echo Executable location: dist\WordleAI.exe
echo.
echo To run the game:
echo   dist\WordleAI.exe
echo.
pause
