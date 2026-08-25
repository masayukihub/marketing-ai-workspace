#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "BLOCKED: project Python is missing at $PYTHON_BIN"
  exit 2
fi

TEMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEMP_ROOT"' EXIT
cp -R "$ROOT/skills/product-knowledge" "$TEMP_ROOT/product-knowledge"

"$PYTHON_BIN" -m pytest -q "$TEMP_ROOT/product-knowledge/tests"
"$PYTHON_BIN" -m pytest -q "$ROOT/skills/switchbot-campaign-review/tests"
"$PYTHON_BIN" -m pytest -q "$ROOT/skills/customer-review-intelligence/tests"

node "$ROOT/skills/amazon-japan-pdp-generator/tests/production_safety_regression.mjs"
node "$ROOT/skills/amazon-japan-pdp-generator/tests/reference_system_regression.mjs"

find "$ROOT/skills/edm-generator" -type f -name '*.rb' -print0 | xargs -0 -n1 ruby -c >/dev/null
echo "PASS skill tests and EDM Ruby syntax checks"
