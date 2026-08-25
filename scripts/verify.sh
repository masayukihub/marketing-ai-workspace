#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "BLOCKED: project Python is missing at $PYTHON_BIN"
  echo "Create $ROOT/.venv and install requirements-dev.txt; system Python is not an accepted fallback."
  exit 2
fi

cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1

"$PYTHON_BIN" -c 'import sys; assert sys.version_info >= (3, 11), sys.version'
"$PYTHON_BIN" -m pytest -q flows/product-onboarding/tests
"$PYTHON_BIN" tests/validate_workspace.py --check all
PYTHON_BIN="$PYTHON_BIN" bash tests/run_skill_tests.sh

if git ls-files | grep -Eq '(^|/)(source-snapshot|product-knowledge-change-proposal|product-truth-proposal|conflict-missing-report|claim-human-review-queue|run-manifest)\.json$|(^|/)product-truth-review\.html$'; then
  echo "BLOCKED: a real Product Onboarding runtime artifact is tracked by Git"
  exit 1
fi

git diff --check
echo "PASS: unified workspace verification via $PYTHON_BIN"
