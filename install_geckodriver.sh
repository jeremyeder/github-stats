#!/bin/bash

# Install geckodriver for macOS
echo "Installing geckodriver for macOS..."

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "jq is required but not installed. Installing jq..."
    if command -v brew &> /dev/null; then
        brew install jq
    else
        echo "Homebrew not found. Please install jq manually:"
        echo "  brew install jq"
        echo "  or download from: https://stedolan.github.io/jq/"
        exit 1
    fi
fi

# Get the latest release info from GitHub API
echo "Fetching latest geckodriver release info..."
API_URL="https://api.github.com/repos/mozilla/geckodriver/releases/latest"
RELEASE_INFO=$(curl -s "$API_URL")

if [ $? -ne 0 ]; then
    echo "Failed to fetch release information"
    exit 1
fi

# Extract download URL for macOS
DOWNLOAD_URL=$(echo "$RELEASE_INFO" | jq -r '.assets[] | select(.name | contains("macos")) | .browser_download_url' | head -1)

if [ -z "$DOWNLOAD_URL" ] || [ "$DOWNLOAD_URL" = "null" ]; then
    echo "Could not find macOS download URL. Trying alternative approach..."
    # Fallback: look for any .tar.gz file that might be macOS
    DOWNLOAD_URL=$(echo "$RELEASE_INFO" | jq -r '.assets[] | select(.name | contains("tar.gz")) | .browser_download_url' | head -1)
fi

if [ -z "$DOWNLOAD_URL" ] || [ "$DOWNLOAD_URL" = "null" ]; then
    echo "Could not find suitable download URL"
    echo "Available assets:"
    echo "$RELEASE_INFO" | jq -r '.assets[].name'
    exit 1
fi

echo "Downloading geckodriver from: $DOWNLOAD_URL"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download and extract
curl -L -o geckodriver.tar.gz "$DOWNLOAD_URL"
tar -xzf geckodriver.tar.gz

# Make executable
chmod +x geckodriver

# Move to /usr/local/bin (or current directory if no permission)
if [ -w /usr/local/bin ]; then
    mv geckodriver /usr/local/bin/
    echo "geckodriver installed to /usr/local/bin/geckodriver"
else
    mv geckodriver "$OLDPWD/"
    echo "geckodriver installed to current directory (no write permission for /usr/local/bin)"
    echo "To use globally, run: sudo mv geckodriver /usr/local/bin/"
fi

# Clean up
cd "$OLDPWD"
rm -rf "$TEMP_DIR"

# Verify installation
echo "Verifying installation..."
if command -v geckodriver &> /dev/null; then
    echo "✅ geckodriver successfully installed!"
    geckodriver --version
else
    echo "⚠️  geckodriver may not be in PATH. Check installation location."
fi