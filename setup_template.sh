#!/bin/bash
# Diamond Brain — Quick Setup
# Copies brain module into your project's scripts/ directory

TARGET="${1:-.}"
echo "Installing Diamond Brain into: $TARGET/scripts/brain/"

mkdir -p "$TARGET/scripts/brain/memory"
cp brain/__init__.py "$TARGET/scripts/brain/"
cp brain/diamond_brain.py "$TARGET/scripts/brain/"
cp zombie_audit.py "$TARGET/scripts/"

echo "Done! Edit scripts/zombie_audit.py to set your project root."
echo "Run: python scripts/zombie_audit.py --brain-status"
