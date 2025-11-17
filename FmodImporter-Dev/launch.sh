#!/bin/bash
# ============================================
# FMOD Importer Tool - macOS/Linux Launcher (DEV)
# ============================================

echo ""
echo "========================================"
echo "   FMOD Importer Tool (Development)"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo ""
    echo "Installation:"
    echo "  - macOS: brew install python3"
    echo "  - Ubuntu/Debian: sudo apt-get install python3"
    echo "  - Fedora: sudo dnf install python3"
    echo ""
    exit 1
fi

echo "Python detected:"
python3 --version
echo ""

# Check tkinter (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    python3 -c "import tkinter" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "WARNING: tkinter is not installed"
        echo "Install it with:"
        echo "  Ubuntu/Debian: sudo apt-get install python3-tk"
        echo "  Fedora: sudo dnf install python3-tkinter"
        echo ""
        exit 1
    fi
fi

# Launch the application
echo "Launching FMOD Importer Tool..."
echo ""
python3 fmod_importer.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR launching the application"
    echo ""
    read -p "Press Enter to continue..."
fi
