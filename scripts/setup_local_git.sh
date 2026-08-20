#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
git config core.hooksPath .githooks
chmod +x .githooks/pre-push
echo "Configured versioned Git hooks at .githooks"
