# Security

Wheel of Fish TV is a **single-household** self-hosted app. One install holds one `WOF_SECRET_KEY`, one media-server connection, and encrypted Plex/Jellyfin tokens in the database. It is not designed as multi-tenant SaaS.

## Reporting vulnerabilities

If you discover a security issue, please report it privately (GitHub Security Advisories on this repository, or contact the maintainer listed in the repo). Do not open public issues for undisclosed vulnerabilities.

## Automated checks (CI)

Every push and pull request to `main` runs [`.github/workflows/security.yml`](.github/workflows/security.yml):

| Check | Tool | Purpose |
|-------|------|---------|
| Secret scan | [Gitleaks](https://github.com/gitleaks/gitleaks) | Detect committed API keys, tokens, and high-entropy secrets |
| SAST | [Semgrep](https://semgrep.dev/) | Python/FastAPI/OWASP rules on application source |
| Python dependencies | [pip-audit](https://pypi.org/project/pip-audit/) | Known CVEs in locked backend dependencies |
| Frontend dependencies | `npm audit` | High/critical issues in the SPA lockfile |
| API auth guards | `pytest tests/security` | Unauthenticated requests get `401` on protected `/api/v1` routes |
| Container image | [Trivy](https://github.com/aquasecurity/trivy) | CRITICAL/HIGH CVEs in the production Docker image |

Lint, unit tests, and Compose smoke tests run separately in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Run checks locally

**One command** (Python + npm + Gitleaks via Docker if `gitleaks` is not on your PATH):

```bash
chmod +x scripts/security-local.sh
./scripts/security-local.sh
```

Or step by step:

```bash
cd backend && uv sync
uv run pytest tests/security -q
uv export --frozen --no-dev --no-emit-project -o /tmp/wof-audit-requirements.txt
uv run pip-audit -r /tmp/wof-audit-requirements.txt

cd frontend && nvm use   # .nvmrc pins Node 22 (matches CI; avoids EBADENGINE on Node 23)
npm ci && npm audit --audit-level=high

# Gitleaks: brew install gitleaks, OR Docker without a local install:
docker run --rm -v "$(pwd):/repo" -w /repo ghcr.io/gitleaks/gitleaks:v8.24.2 \
  detect --source /repo --config /repo/.gitleaks.toml

docker build -f backend/Dockerfile -t wheeloffishtv:local .
trivy image --severity CRITICAL,HIGH wheeloffishtv:local

# Semgrep — no install required if you have Docker:
./scripts/semgrep-local.sh
# or:
docker run --rm -v "$(pwd):/src" -w /src semgrep/semgrep:latest \
  semgrep scan --config p/python --config p/fastapi --config p/owasp-top-ten backend/src
# Native: brew install semgrep && ./scripts/semgrep-local.sh
```

### Interpreting output

| Message | Meaning |
|---------|---------|
| `wheeloffish … not found on PyPI` (pip-audit) | Expected when auditing the local package; use `uv export --no-emit-project` (as in the script above) to audit only locked dependencies. |
| `EBADENGINE` / Node `v23.x` (npm) | ESLint targets Node 20.19+, **22.13+**, or **24+**. Node 23 is unsupported. Use `nvm use` in `frontend/` (see `.nvmrc`). CI uses Node 22. |
| `26 passed, N warnings` (auth guard tests) | Tests pass; warnings from a single Alembic migration run are normal. Re-running migrations once per session keeps noise low. |
| `command not found: gitleaks` | Install with Homebrew or use the Docker command above; CI installs Gitleaks automatically. |
| `MAL-2026-4750` on `fastapi==0.136.3` (pip-audit) | Amazon Inspector flagged that PyPI release; upstream treats `fastar` in `[standard]` as intentional. This app installs plain `fastapi` (not `[standard]`). Backend pins `fastapi==0.136.1` until a newer release clears the advisory ([#1](https://github.com/jwposton/wheeloffishtv/issues/1)). |

## Operator hardening

Before exposing the app to your LAN or the internet:

1. **Generate a unique `WOF_SECRET_KEY`** per install (`openssl rand -hex 32`). Anyone with this key and a copy of `/data` can decrypt stored media-server tokens.
2. **Terminate TLS** at a reverse proxy (Caddy, Traefik, nginx). Set `WOF_OAUTH_CALLBACK_BASE` to the public HTTPS URL users hit in the browser.
3. **Set `ENVIRONMENT=production`** so session cookies use `Secure` / HTTPS-only semantics.
4. **Configure admin** via `WOF_ADMIN_PROVIDER_USER_ID` (and optionally `WOF_ADMIN_USERNAME`) after first OAuth login; avoid leaving setup mode open on a reachable host.
5. **Do not publish port 8000** to the open internet until admin and library scope are configured.
6. **Treat backups as secret**: `wheeloffish.db` (or Postgres) contains Fernet-encrypted tokens; protect backup storage like credentials.
7. **Keep images updated**: pull new `ghcr.io` tags when releases include security fixes.

## Trust boundaries

| Asset | Risk if exposed |
|-------|-----------------|
| `WOF_SECRET_KEY` | Decrypt all vault secrets for that install |
| Session cookie | Act as that app user (playlist/catalog APIs) |
| Plex/Jellyfin user token (vault) | API access as that user on the linked media server |
| `.env` on disk | Connection URL, admin IDs, encryption key |

The app stores provider tokens with Fernet (`SecretsVault`) keyed by `WOF_SECRET_KEY`. Logs should not contain raw tokens; report any leak in application logging.

## What automation does not cover

- OAuth redirect URL misconfiguration (`WOF_OAUTH_CALLBACK_BASE`)
- Reverse-proxy header/trust mistakes
- Host filesystem permissions on `/data`
- Plex/Jellyfin account compromise outside this app

Use staging + [OWASP ZAP](https://www.zaproxy.org/) baseline scans when you change auth or proxy layout.
