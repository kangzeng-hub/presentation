#!/usr/bin/env bash
set -euo pipefail
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
printf '========================================\nPresentation System Smoke Test\n========================================\n'
if curl --fail --silent --show-error "$FRONTEND_URL" >/dev/null; then
  echo "✓ Frontend reachable"
else
  echo "✗ Frontend unreachable: $FRONTEND_URL" >&2
  exit 1
fi
health="$(curl --fail --silent --show-error "$BACKEND_URL/health")"
echo "$health" | grep -q '"status":"ok"' && echo "✓ Backend reachable" && echo "✓ Health check passed"
demo="$(curl --fail --silent --show-error "$BACKEND_URL/projects/demo-project")"
echo "$demo" | grep -q 'demo-project' && echo "✓ Demo data loaded"
echo "Smoke test passed."
