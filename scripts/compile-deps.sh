#!/usr/bin/env bash
# Recompile requirements.txt from requirements.in using uv (fast Rust-based resolver)
# Usage: ./scripts/compile-deps.sh
#
# uv is ~100x faster than pip-compile and produces identical output format.
# Install uv: pip install uv  OR  curl -LsSf https://astral.sh/uv/install.sh | sh

set -euo pipefail

echo "Compiling requirements.txt from requirements.in..."
uv pip compile requirements.in \
    --generate-hashes \
    --output-file requirements.txt \
    --annotation-style line \
    --python-version 3.11

echo "Done! requirements.txt updated."
