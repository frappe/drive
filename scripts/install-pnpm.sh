#!/bin/bash
set -euo pipefail

if ! command -v pnpm &> /dev/null; then
    echo "pnpm could not be found, installing..."
    npm install -g pnpm@latest-10
fi

if ! command -v pnpm &> /dev/null; then
    echo "ERROR: pnpm installation failed, binary still not found in PATH" >&2
    exit 1
fi

echo "pnpm version: $(pnpm --version)"
