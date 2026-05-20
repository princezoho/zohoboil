#!/bin/bash
# Line Boil Effect - Installer
# Double-click this file to install

cd "$(dirname "$0")"

echo "================================"
echo "Line Boil Effect - Installing..."
echo "================================"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    echo "Please install Python 3 from https://www.python.org/downloads/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "WARNING: ffmpeg not found. Audio will not be preserved."
    echo "To install ffmpeg: brew install ffmpeg"
    echo ""
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate and install
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install opencv-python numpy flask > /dev/null 2>&1

echo ""
echo "================================"
echo "Installation complete!"
echo "================================"
echo ""
echo "To run the app, double-click: run.command"
echo ""
read -p "Press Enter to exit..."
