#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
fail=0
printf '========================================\nGitHub Release Check\n========================================\n'
if [[ -f .env ]]; then echo "✓ .env exists locally (must stay gitignored)"; else echo "! .env missing; copy .env.example to .env if you need real providers"; fi
"$ROOT/scripts/secret_scan.sh" || fail=1
[[ -f .gitignore && -f .dockerignore && -f .env.example ]] && echo "✓ Git/Docker boundary and env template" || fail=1
"$ROOT/scripts/test.sh" || fail=1
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose config -q || fail=1
else
  echo "! Docker unavailable; skipped compose validation"
fi
NPM_CONFIG_CACHE="${NPM_CONFIG_CACHE:-/tmp/presentation-npm-cache}" npm --prefix frontend ci || fail=1
npm --prefix frontend run build || fail=1
if [[ "$fail" -eq 0 ]]; then echo "READY FOR GITHUB (after reviewing git status)"; else echo "RELEASE BLOCKED"; fi
exit "$fail"
