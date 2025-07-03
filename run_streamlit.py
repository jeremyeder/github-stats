#!/usr/bin/env python3
"""Script to run the Streamlit application."""

import sys
import subprocess


def main():
    """Run the Streamlit application."""
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "streamlit_app/app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\nStreamlit app stopped.")
    except Exception as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()