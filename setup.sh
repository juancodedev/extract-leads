#!/usr/bin/env bash
set -e

echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║     Lead Extractor — Setup                ║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Install it from: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate and install deps
source .venv/bin/activate
echo "🔧 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Check for API key
if [ -z "$GOOGLE_PLACES_API_KEY" ]; then
    echo ""
    echo "⚠️  GOOGLE_PLACES_API_KEY is not set."
    echo "   Get a free key at: https://console.cloud.google.com"
    echo "   Then set it: export GOOGLE_PLACES_API_KEY='your_key'"
    echo ""
else
    echo "✓ GOOGLE_PLACES_API_KEY is set"
fi

echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║  Setup complete!                          ║"
echo "  ║                                           ║"
echo "  ║  Run: python pipeline.py --interactive    ║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""
