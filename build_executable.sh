#!/bin/bash
# Build script for creating Wordle executable

echo "🎮 Building Wordle Executable..."
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null
then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Create cache directory if it doesn't exist
if [ ! -d ".cache" ]; then
    echo "📁 Creating cache directory..."
    mkdir -p .cache
fi

# Build feedback table cache if it doesn't exist
if [ ! -f ".cache/feedback_table_2315_"*.pkl ]; then
    echo "🔨 Building feedback table cache (this may take a few seconds)..."
    python -c "from wordle.feedback_table import FeedbackTable; from wordle.words import WORD_LIST; FeedbackTable.build_or_load(WORD_LIST)"
fi

echo "🔧 Building executable with PyInstaller..."
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
echo "✅ Build complete!"
echo ""
echo "📍 Executable location: dist/WordleAI"
echo ""
echo "To run the game:"
echo "  ./dist/WordleAI          (Linux/Mac)"
echo "  dist\\WordleAI.exe       (Windows)"
