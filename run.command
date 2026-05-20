#!/bin/bash
# Line Boil Effect - Run
# Double-click this file to start the app

cd "$(dirname "$0")"

# Check if installed
if [ ! -d "venv" ]; then
    echo "App not installed yet. Please run install.command first."
    read -p "Press Enter to exit..."
    exit 1
fi

echo "================================"
echo "Line Boil Effect"
echo "================================"
echo ""
echo "Starting server..."
echo "Opening browser to http://localhost:5050"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

source venv/bin/activate

# Open browser after a short delay
(sleep 2 && open http://localhost:5050) &

python3 app.py
