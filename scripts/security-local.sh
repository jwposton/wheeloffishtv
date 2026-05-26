#!/usr/bin/env bash
# Run the same security checks as CI where possible (no global gitleaks/semgrep/trivy required).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

GITLEAKS_IMAGE="${GITLEAKS_IMAGE:-ghcr.io/gitleaks/gitleaks:v8.24.2}"
SEMGREP_IMAGE="${SEMGREP_IMAGE:-semgrep/semgrep:latest}"

run_semgrep() {
  echo "==> SAST (Semgrep)"
  local -a args=(
    scan
    --config p/python
    --config p/fastapi
    --config p/owasp-top-ten
    backend/src
  )
  if command -v semgrep >/dev/null 2>&1; then
    semgrep "${args[@]}"
  elif command -v docker >/dev/null 2>&1; then
    docker run --rm -v "${ROOT}:/src" -w /src "${SEMGREP_IMAGE}" semgrep "${args[@]}"
  else
    echo "Skip: install semgrep (brew install semgrep) or Docker for SAST" >&2
    return 1
  fi
}

run_gitleaks() {
  echo "==> Secret scan (Gitleaks)"
  if command -v gitleaks >/dev/null 2>&1; then
    gitleaks detect --source . --config .gitleaks.toml
  elif command -v docker >/dev/null 2>&1; then
    docker run --rm -v "${ROOT}:/repo" -w /repo "${GITLEAKS_IMAGE}" \
      detect --source /repo --config /repo/.gitleaks.toml
  else
    echo "Skip: install gitleaks (brew install gitleaks) or Docker for secret scan" >&2
    return 1
  fi
}

echo "==> Python auth guards + pip-audit"
(
  cd backend
  audit_req="$(mktemp)"
  trap 'rm -f "$audit_req"' EXIT
  uv sync --quiet
  uv run pytest tests/security -q
  # Write lockfile export to a temp file only (avoid dumping hashes to the terminal).
  uv export --frozen --no-dev --no-emit-project --no-hashes --no-header -q -o "$audit_req"
  echo "    pip-audit: scanning locked dependencies..."
  uv run pip-audit -r "$audit_req" --format columns
)

echo "==> Frontend npm audit (Node 22 recommended — see frontend/.nvmrc)"
(
  cd frontend
  node_major="$(node -p "process.versions.node.split('.')[0]")"
  if [ "$node_major" = "23" ]; then
    echo "    note: Node 23 is unsupported by ESLint; run 'nvm use' here to match CI (Node 22)" >&2
  fi
  npm ci --no-fund
  npm audit --audit-level=high
)

run_semgrep
run_gitleaks

echo "==> All local security checks passed"
echo "    Optional: docker build -f backend/Dockerfile -t wheeloffishtv:local && \\"
echo "              trivy image --severity CRITICAL,HIGH --ignore-unfixed wheeloffishtv:local"
