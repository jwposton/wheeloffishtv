# Phase 3 — Manual UAT Checklist

Operator verification of the minimal SPA shell. Run after automated CI is green:

```bash
cd backend && uv run ruff check . && uv run pytest && cd ../frontend && npm run test -- --run && npm run build
```

**Prerequisites:** `.env` configured with `WOF_SECRET_KEY`, `WOF_PROVIDER`, `WOF_MEDIA_SERVER_URL`, and `WOF_OAUTH_CALLBACK_BASE` reachable from the browser. At least one TV library with watch history on the configured provider.

> **Note (2026-05-26):** Admin env vars (`WOF_ADMIN_*`), `/setup/admin`, and the non-admin holding page were removed. Use the scenarios below for current behavior.

| # | Scenario | Requirement | Steps | Expected | PASS/FAIL | Date | Operator notes |
|---|----------|-------------|-------|----------|-----------|------|----------------|
| 1 | Plex OAuth E2E | WEB-01, D-01 | 1. Start stack with `WOF_PROVIDER=plex`<br>2. Open app login page<br>3. Complete Plex PIN OAuth flow | Session established; redirected to Library (`/browse`) | | | |
| 2 | Jellyfin credential login | WEB-01, D-01 | 1. Start stack with `WOF_PROVIDER=jellyfin`<br>2. Open app login page<br>3. Submit username/password for your Jellyfin server | Session established; redirected to Library | | | |
| 3 | Default library scope | WEB-01 | 1. Sign in as a new user (or clear in-scope flags in DB)<br>2. Wait for background catalog sync<br>3. Open Library | All TV libraries for that account in scope; series appear after sync | | | |
| 4 | Library scope UI | WEB-01, D-11 | 1. Open **Settings → Libraries**<br>2. Toggle in-scope checkboxes; save<br>3. Refresh page | Selection persists; Browse shows series only from in-scope libraries | | | |
| 5 | Unscoped redirect | WEB-01 | 1. Sign in with zero in-scope libraries (uncheck all in Settings → Libraries)<br>2. Navigate to `/browse` | Redirect to **Settings → Libraries** (not an admin holding page) | | | |
| 6 | Browse infinite scroll + search | WEB-01, D-14 | 1. Open `/browse` with scoped libraries<br>2. Scroll to load more pages<br>3. Type in search box | Additional series load; debounced search filters titles | | | |
| 7 | Sync banner | WEB-01, D-15 | 1. Trigger catalog sync (session refresh or API)<br>2. Stay on `/browse` during sync | Top banner shows “Updating library…”; stale cached series remain visible below | | | |
| 8 | Keyboard navigation | WEB-01, ROADMAP a11y | 1. Open `/browse` grid view<br>2. Tab through series cards until one is focused<br>3. Press **Enter** on a focused card | Focus ring visible on cards; Enter opens `/series/{id}` detail page | | | |
| 9 | Series detail resume preview | WEB-01, D-16 | 1. From browse, open a series with watch history<br>2. Review resume/up-next section | Detail shows series metadata and read-only resume preview; **no** playlist or rebuild controls on detail alone | | | |
| 10 | Light/dark theme | WEB-01, D-18 | 1. Toggle theme in header<br>2. Reload page<br>3. (Optional) Change OS `prefers-color-scheme` with no saved preference | Theme switches immediately; preference persists across reload | | | |
| 11 | Connection read-only display | WEB-01, D-08 | 1. Open Settings | Shows connected server URL from configuration; instructs operator to edit `.env` + restart to change | | | |
| 12 | Settings nav for linked users | WEB-01 | 1. Sign in with a linked media account<br>2. Check header nav | **Settings** link visible (not admin-only) | | | |

## Sign-off

| Field | Value |
|-------|-------|
| Operator | |
| Environment | |
| Provider | Plex / Jellyfin |
| All scenarios PASS | ☐ Yes ☐ No |
| Blockers | |

---
*Phase: 03-minimal-operator-spa-shell · Plan: 03-07 · UAT rows updated 2026-05-26 (per-user library scope)*
