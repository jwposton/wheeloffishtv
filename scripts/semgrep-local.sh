#!/usr/bin/env bash
# Semgrep only — matches CI rulesets; uses Docker if semgrep is not installed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SEMGREP_IMAGE="${SEMGREP_IMAGE:-semgrep/semgrep:latest}"
ARGS=(
  scan
  --config p/python
  --config p/fastapi
  --config p/owasp-top-ten
  backend/src
)

if command -v semgrep >/dev/null 2>&1; then
  exec semgrep "${ARGS[@]}"
fi

if command -v docker >/dev/null 2>&1; then
  exec docker run --rm -v "${ROOT}:/src" -w /src "${SEMGREP_IMAGE}" semgrep "${ARGS[@]}"
fi

echo "Install Semgrep or Docker:" >&2
echo "  brew install semgrep" >&2
echo "  # or:" >&2
echo "  docker pull ${SEMGREP_IMAGE}" >&2
exit 1
