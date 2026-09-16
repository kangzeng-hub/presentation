#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ "$#" -gt 0 ]]; then
  # Preserve the ability to run one module or test class explicitly.
  exec "${PYTHON_BIN:-python3}" -m unittest "$@"
fi
exec "${PYTHON_BIN:-python3}" -m unittest discover -s tests -p 'test_*.py'
