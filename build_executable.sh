#!/bin/bash
# Build script for creating Wordle executable

echo "Building Wordle Executable..."
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null
then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Create cache directory if it doesn't exist
if [ ! -d ".cache" ]; then
    echo "Creating cache directory..."
    mkdir -p .cache
fi

# Build feedback table cache if it doesn't exist
if ls .cache/feedback_table_*_sparse100.pkl 1> /dev/null 2>&1; then
    echo "[OK] Cache already exists"
else
    echo "Building sparse feedback table cache (max 100 connections per word)..."
    python run_cache.py
fi

echo "Building executable with PyInstaller..."
pyinstaller --noconfirm \
    --name "WordleAI" \
    --onefile \
    --windowed \
    --add-data "valid_solutions.csv:." \
    --add-data ".cache:cache" \
    --icon NONE \
    --hidden-import tkinter \
    --hidden-import tkinter.messagebox \
    --collect-all wordle \
    run_game.py

echo ""
echo "[OK] Build complete!"
echo ""
echo "Executable location: dist/WordleAI"
echo ""
echo "To run the game:"
echo "  ./dist/WordleAI          (Linux/Mac)"
echo "  dist\\WordleAI.exe       (Windows)"
