#!/bin/bash
# Setup script for Parser Generator

echo "================================================================"
echo "Personal Banking Parser Generator - Setup"
echo "================================================================"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please create one first: python3 -m venv venv"
    exit 1
fi

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "WARNING: ANTHROPIC_API_KEY environment variable not set"
    echo
    echo "You need an Anthropic API key to use the parser generator."
    echo "Get one at: https://console.anthropic.com/"
    echo
    echo "Then set it:"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
    echo "  Or add to .env file: echo 'ANTHROPIC_API_KEY=your-key-here' >> .env"
    echo
fi

# Install dependencies
echo "Installing dependencies..."
venv/bin/pip install -q crewai crewai-tools anthropic pyyaml

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Create parser_generator directory if it doesn't exist
if [ ! -d "parser_generator" ]; then
    mkdir parser_generator
    echo "✓ Created parser_generator directory"
fi

# Check if agent.py exists
if [ ! -f "parser_generator/agent.py" ]; then
    echo "✗ parser_generator/agent.py not found!"
    echo "  Make sure you have the agent.py file in the parser_generator directory"
    exit 1
else
    echo "✓ Found parser_generator/agent.py"
fi

# Check if institutions.yaml exists
if [ ! -f "institutions.yaml" ]; then
    echo "✗ institutions.yaml not found!"
    echo "  Make sure you have the institutions.yaml configuration file"
    exit 1
else
    echo "✓ Found institutions.yaml"
fi

# Check if parser_loader.py exists
if [ ! -f "parser_loader.py" ]; then
    echo "✗ parser_loader.py not found!"
    echo "  Make sure you have the parser_loader.py file"
    exit 1
else
    echo "✓ Found parser_loader.py"
fi

# Test the parser loader
echo
echo "Testing parser loader..."
venv/bin/python parser_loader.py list > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Parser loader works correctly"
else
    echo "✗ Parser loader test failed"
    exit 1
fi

# Show configured institutions
echo
echo "Configured institutions:"
venv/bin/python parser_loader.py list | grep -A 3 "^[A-Z]" | head -20

echo
echo "================================================================"
echo "Setup complete!"
echo "================================================================"
echo
echo "Quick start:"
echo "  1. Place PDFs: mkdir statements/NewBank && cp *.pdf statements/NewBank/"
echo "  2. Generate parser: venv/bin/python parser_generator/agent.py NewBank"
echo "  3. Test parser: venv/bin/python parser_loader.py test statements/NewBank/file.pdf"
echo "  4. Process statements: venv/bin/python process_statements.py process"
echo
echo "For detailed instructions, see: PARSER_GENERATOR_README.md"
echo
