#!/bin/bash
"""Start the GitHub Stats Streamlit Dashboard"""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🚀 Starting GitHub Stats Dashboard..."
    echo "📊 Dashboard will be available at: http://localhost:8501"
    echo "💡 Press Ctrl+C to stop the dashboard"
    echo ""
    
    # Activate virtual environment and run Streamlit
    source venv/bin/activate
    python -m streamlit run streamlit_app/app.py --server.port 8501 --server.address localhost
else
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -e ."
    exit 1
fi