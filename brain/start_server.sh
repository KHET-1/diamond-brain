#!/usr/bin/env bash
cd "$(dirname "$0")/.."
python brain/server.py --memory-dir brain/memory-forensic "$@"
