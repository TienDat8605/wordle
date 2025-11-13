@echo off
REM Build script for creating Wordle executable on Windows

echo Building Wordle Executable for Windows...
echo.

REM Check if Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH. Please install Python and retry.
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

REM Create cache directory if it doesn't exist
if not exist ".cache" (
    echo Creating cache directory...
    mkdir .cache
)

REM Build feedback table cache
echo Building feedback table cache...
python -c "from wordle.feedback_table import FeedbackTable; from wordle.words import WORD_LIST; FeedbackTable(WORD_LIST)"

echo.
echo Running PyInstaller...
echo.
python -m PyInstaller --noconfirm ^
    --name "WordleAI" ^
    --onefile ^
    --windowed ^
    --add-data "valid_solutions.csv;." ^
    --add-data ".cache;.cache" ^
    --icon NONE ^
    --hidden-import tkinter ^
    --hidden-import tkinter.messagebox ^
    --collect-all wordle ^
    run_game.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo Build complete!
echo Executable location: dist\WordleAI.exe
echo.
pause
