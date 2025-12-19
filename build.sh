#!/bin/bash
# Build script for Render deployment

echo "🚀 Installing Playwright..."
python -m playwright install chromium --with-deps

echo "✅ Build complete!"
