#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
fail=0
ok(){ printf '✓ %s\n' "$1"; }
bad(){ printf '✗ %s\n' "$1"; fail=1; }
printf '========================================\nPresentation System Doctor\n========================================\n'
command -v docker >/dev/null 2>&1 && ok "Docker" || printf '! Docker unavailable (local Python/Node checks can still run)\n'
docker compose version >/dev/null 2>&1 && ok "Docker Compose" || printf '! Docker Compose unavailable (container checks skipped)\n'
[[ -f .env.example ]] && ok ".env.example" || bad ".env.example is missing"
[[ -f .gitignore && -f .dockerignore ]] && ok "Git and Docker boundaries" || bad ".gitignore or .dockerignore is missing"
[[ -f examples/demo_sku/product.json && -f examples/demo_sku/competitor_evidence.json ]] && ok "Demo data" || bad "Demo data is incomplete"
[[ -f frontend/package-lock.json && -f backend/requirements.txt ]] && ok "Dependency manifests" || bad "Dependency manifests are incomplete"
[[ -d frontend && -d backend && -d scripts ]] && ok "Project structure" || bad "Project structure is incomplete"
if [[ $fail -eq 0 ]]; then printf '\nSystem is ready.\n'; else printf '\nSystem is not ready. Follow the fixes above.\n'; fi
exit "$fail"
