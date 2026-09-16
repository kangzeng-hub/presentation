#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"
[[ -x "$PYTHON_BIN" ]] || PYTHON_BIN="${PYTHON_BIN_FALLBACK:-python3}"
CONTRACT="$ROOT/contracts/openapi.yaml"
GENERATED="$ROOT/frontend/src/generated/api.ts"
TMP_OPENAPI="$(mktemp)"
TMP_CLIENT="$(mktemp)"
trap 'rm -f "$TMP_OPENAPI" "$TMP_CLIENT"' EXIT

"$PYTHON_BIN" - "$TMP_OPENAPI" <<'PY'
import json, sys
from backend.main import app
if app is None:
    raise SystemExit("FastAPI app is unavailable")
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(app.openapi(), handle, sort_keys=True)
PY

"$PYTHON_BIN" - "$CONTRACT" "$TMP_OPENAPI" <<'PY'
import json, re, sys
from pathlib import Path

contract = Path(sys.argv[1]).read_text(encoding="utf-8")
actual = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
expected_paths = set(re.findall(r"^  (/[^:]+):$", contract, re.MULTILINE))
actual_paths = set(actual.get("paths", {}))
missing = sorted(expected_paths - actual_paths)
if missing:
    raise SystemExit("Missing FastAPI paths: " + ", ".join(missing))
expected_methods = {}
current_path = None
for line in contract.splitlines():
    path_match = re.match(r"^  (/[^:]+):$", line)
    if path_match:
        current_path = path_match.group(1)
        expected_methods[current_path] = set()
        continue
    method_match = re.match(r"^    (get|post|put|patch|delete):$", line)
    if current_path and method_match:
        expected_methods[current_path].add(method_match.group(1))
method_drift = {
    path: sorted(methods - set(actual["paths"].get(path, {})))
    for path, methods in expected_methods.items()
    if methods - set(actual["paths"].get(path, {}))
}
if method_drift:
    raise SystemExit("Missing FastAPI methods: " + repr(method_drift))
required_schemas = {"Project", "ProductTruth", "CompetitorSnapshot", "CompetitorInsight", "PresentationStrategy", "ArtifactVersion", "Job", "Approval", "ExportManifest", "ErrorResponse", "QAReport"}
missing_schemas = sorted(required_schemas - set(actual.get("components", {}).get("schemas", {})))
if missing_schemas:
    raise SystemExit("Missing FastAPI schemas: " + ", ".join(missing_schemas))
print(f"✓ FastAPI OpenAPI paths={len(actual_paths)} schemas={len(actual.get('components', {}).get('schemas', {}))}")
PY

command -v npx >/dev/null 2>&1 || { echo "npx is required for contract generation" >&2; exit 1; }
npx --yes openapi-typescript@7.9.1 "$CONTRACT" -o "$TMP_CLIENT" >/dev/null
cmp -s "$TMP_CLIENT" "$GENERATED" || {
  echo "Generated TypeScript client is stale. Run:" >&2
  echo "npx openapi-typescript@7.9.1 contracts/openapi.yaml -o frontend/src/generated/api.ts" >&2
  exit 1
}
echo "✓ OpenAPI contract and generated TypeScript client are synchronized"
