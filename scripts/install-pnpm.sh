#!/bin/bash

if ! command -v pnpm &> /dev/null
then
    echo "pnpm could not be found, installing..."
    npm install -g pnpm@latest-10
else
    echo "pnpm is already installed."
fi

echo "pnpm version: $(pnpm --version)"

exit 0