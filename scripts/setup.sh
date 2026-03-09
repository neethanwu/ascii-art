#!/usr/bin/env bash
# ASCII Art Converter — Environment Setup
# Idempotent: safe to run multiple times

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
MARKER="$SCRIPT_DIR/.setup_done"
REQUIRED_PYTHON_MAJOR=3
REQUIRED_PYTHON_MINOR=8

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[ascii-art]${NC} $1"; }
warn()  { echo -e "${YELLOW}[ascii-art]${NC} $1"; }
error() { echo -e "${RED}[ascii-art]${NC} $1" >&2; }

# Fast path: already set up
if [ -f "$MARKER" ]; then
    # Verify venv still exists and works
    if [ -f "$VENV_DIR/bin/python" ] && "$VENV_DIR/bin/python" -c "import PIL, numpy, pyfiglet" 2>/dev/null; then
        exit 0
    fi
    # Marker exists but env is broken — re-setup
    rm -f "$MARKER"
    warn "Environment needs repair, re-running setup..."
fi

# Step 1: Find Python 3.8+
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge "$REQUIRED_PYTHON_MAJOR" ] && [ "$minor" -ge "$REQUIRED_PYTHON_MINOR" ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    error "Python ${REQUIRED_PYTHON_MAJOR}.${REQUIRED_PYTHON_MINOR}+ is required but not found."
    echo ""
    echo "Install Python:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install python3"
    elif [[ "$OSTYPE" == "linux"* ]]; then
        echo "  sudo apt install python3 python3-venv python3-pip"
    fi
    exit 1
fi

info "Found $PYTHON ($($PYTHON --version 2>&1))"

# Step 2: Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR" 2>/dev/null || {
        # venv module might not be installed on some Linux distros
        error "Failed to create venv. On Linux, try: sudo apt install python3-venv"
        exit 1
    }
fi

# Activate venv
PIP="$VENV_DIR/bin/pip"
VPYTHON="$VENV_DIR/bin/python"

# Step 3: Ensure pip is available
if [ ! -f "$PIP" ]; then
    info "Installing pip..."
    "$VPYTHON" -m ensurepip --upgrade 2>/dev/null || {
        error "Failed to install pip. Try: $PYTHON -m ensurepip --upgrade"
        exit 1
    }
fi

# Step 4: Install required packages
info "Installing dependencies..."
"$PIP" install --quiet --upgrade pip 2>/dev/null || true
"$PIP" install --quiet pillow numpy pyfiglet

# Step 5: Install optional packages (non-fatal)
if "$PIP" install --quiet opencv-python-headless 2>/dev/null; then
    info "Installed opencv (video support enabled)"
else
    warn "opencv-python not installed — video conversion unavailable"
    warn "To enable: $PIP install opencv-python-headless"
fi

# Step 6: Verify
"$VPYTHON" -c "
import PIL, numpy, pyfiglet
print('  pillow', PIL.__version__)
print('  numpy', numpy.__version__)
print('  pyfiglet', pyfiglet.__version__)
try:
    import cv2
    print('  opencv', cv2.__version__)
except ImportError:
    print('  opencv: not installed (optional)')
"

# Mark as done
touch "$MARKER"
info "Setup complete!"
