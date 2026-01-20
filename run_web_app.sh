#!/bin/bash
# Startup script for the Portfolio Query Web Interface

cd "$(dirname "$0")"

echo "Starting Portfolio Query Web Interface..."
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if required packages are installed
echo "Checking dependencies..."
python -c "import flask" 2>/dev/null || {
    echo "Flask not found. Installing dependencies..."
    pip install -r requirements.txt
}

# Set Flask app
export FLASK_APP=web.app
export FLASK_ENV=development

# Run the application
echo ""
echo "Starting web server on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

python -m web.app

