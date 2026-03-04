#!/bin/bash
# Diamond Brain v3.0 — Quick Setup
# Copies brain module into your project's scripts/ directory

TARGET="${1:-.}"
echo "Installing Diamond Brain v3.0 into: $TARGET/scripts/brain/"

mkdir -p "$TARGET/scripts/brain/memory"
cp brain/__init__.py "$TARGET/scripts/brain/"
cp brain/diamond_brain.py "$TARGET/scripts/brain/"
cp brain/server.py "$TARGET/scripts/brain/"
cp sentinel_audit.py "$TARGET/scripts/"

echo "Done! Edit scripts/sentinel_audit.py to set your project root."
echo "Run: python scripts/sentinel_audit.py --brain-status"
echo "Server: python scripts/brain/server.py --port 7734"
