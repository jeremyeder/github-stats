#!/bin/bash

# Setup environment for GitHub Stats project
echo "Setting up GitHub Stats environment..."

# Add current directory to PATH for this session
export PATH="$PWD:$PATH"

# Check if geckodriver is available
if command -v geckodriver &> /dev/null; then
    echo "✅ geckodriver is available"
    geckodriver --version
else
    echo "⚠️  geckodriver not found. Run ./install_geckodriver.sh first"
fi

# Check if jq is available
if command -v jq &> /dev/null; then
    echo "✅ jq is available"
    jq --version
else
    echo "⚠️  jq not found. Install with: brew install jq"
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
    echo "Virtual environment activated"
else
    echo "⚠️  Virtual environment not found. Create with: python3 -m venv venv"
fi

echo "Environment setup complete!"
echo "To use geckodriver globally, run: sudo mv geckodriver /usr/local/bin/"