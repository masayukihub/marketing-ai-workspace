#!/usr/bin/env bash
set -euo pipefail

python3 -m unittest discover -s visual-system/tests -p 'test_*.py' -v

python3 -m pytest -q skills/product-knowledge/tests
python3 -m pytest -q skills/switchbot-campaign-review/tests
python3 -m pytest -q skills/customer-review-intelligence/tests
python3 -m pytest -q skills/switchbot-japan-campaign/tests
python3 -m pytest -q skills/switchbot-japan-edm/tests

node skills/amazon-japan-pdp-generator/tests/production_safety_regression.mjs
node skills/amazon-japan-pdp-generator/tests/reference_system_regression.mjs

find skills/edm-generator -type f -name '*.rb' -print0 | xargs -0 -n1 ruby -c >/dev/null
echo "PASS skill tests and EDM Ruby syntax checks"
