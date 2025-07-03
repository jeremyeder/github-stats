#!/usr/bin/env python3
"""Script to run the Streamlit application."""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Run the Streamlit application."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    venv_python = script_dir / "venv" / "bin" / "python"

    # Use virtual environment Python if it exists, otherwise fall back to system Python
    if venv_python.exists():
        python_executable = str(venv_python)
        print(f"Using virtual environment Python: {python_executable}")
    else:
        python_executable = sys.executable
        print(f"Using system Python: {python_executable}")

    try:
        # Change to the script directory to ensure relative paths work
        os.chdir(script_dir)

        subprocess.run(
            [
                python_executable,
                "-m",
                "streamlit",
                "run",
                "streamlit_app/app.py",
                "--server.port",
                "8501",
                "--server.address",
                "localhost",
            ]
        )
    except KeyboardInterrupt:
        print("\nStreamlit app stopped.")
    except Exception as e:
        print(f"Error running Streamlit: {e}")
        print("Make sure Streamlit is installed: pip install streamlit")
        sys.exit(1)


if __name__ == "__main__":
    main()
