# Phase 7 — Validation Strategy

**Release gate:** v0.1.0  
**Requirement:** EXP-01

## Automated verification

| Plan | Command |
|------|---------|
| 07-01 | `cd backend && uv run pytest tests/unit/test_plex_playlist_client.py tests/unit/test_provider_writeback.py tests/unit/test_orchestrator_writeback.py -q` |
| 07-02 | `cd backend && uv run pytest tests/unit/test_jellyfin_playlist_client.py -q` |
| 07-03 | `cd backend && uv run pytest tests/integration/test_playlist_writeback_lifecycle.py -q` |
| Frontend | `cd frontend && npm run test -- --run` |

## Full suite before tag

```bash
cd backend && uv run ruff check . && uv run pytest
cd ../frontend && npm run test -- --run
```

See `07-UAT.md` for manual Plex/Jellyfin smoke tests.
