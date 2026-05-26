# Backlog — Wheel of Fish TV

Deferred work not scheduled in the current phase. Pull items into a phase plan when ready.

**Last updated:** 2026-05-26

---

## Auth & operator model

### BL-02: Remove admin RBAC — per-user library settings for any signed-in user

**Added:** 2026-05-26  
**Target:** Phase 8 or post–v0.1.0 (breaking UX/env change)  
**Component:** `backend/src/wheeloffish/core/auth.py`, `api/deps.py`, `api/routes/catalog.py`, `api/routes/auth.py`, `core/config.py`, `core/catalog_sync.py`, `frontend/src/routes/AdminRoute.tsx`, `LibraryScopeGuard`, `HoldingPage`, `AdminSetupPage`, `AdminSetupPanel`, `AdminLibrarySetupPage`, `AppShell`, `useLibraryScope.ts`, `.env.example`, `README.md`, `SECURITY.md`

**User story:** As someone who can sign in to my own Plex or Jellyfin account against an install I control (or have credentials for), I want to open **Settings → Libraries** and choose which TV libraries appear in Browse—without anyone being designated an “admin” or pasting provider user IDs into `.env`.

**Product intent:**

- **Keep:** Media server connection defined only via Docker Compose / `.env` (`WOF_PROVIDER`, `WOF_MEDIA_SERVER_URL`, etc.) — one server per install, unchanged.
- **Remove:** `WOF_ADMIN_PROVIDER_USER_ID`, `WOF_ADMIN_USERNAME`, setup mode, admin-only routes, admin setup pages, and “wait for admin” holding states.
- **Replace with:** Any authenticated user who has linked their media account manages **their own** library scope (already stored per `app_user_id` on `cached_libraries`).

**Behavior:**

1. **Default scope on first link / first library sync:** When a user has no in-scope libraries yet, mark **all TV libraries** returned by the provider as in-scope. (`list_libraries` already filters to show-type sections on Plex; align Jellyfin the same way.)
2. **Settings for everyone:** `/settings` and `/settings/libraries` available to any signed-in user with a media link (not gated on `is_admin`).
3. **API surface:** Move library list + scope update off `/api/v1/admin/...` to user-scoped routes, e.g. extend existing `GET /api/v1/connections/{id}/libraries` to return all libraries with `in_scope` flags, and add `PUT /api/v1/connections/{id}/library-scope` (session auth only, no `require_admin`).
4. **Remove from `/auth/me`:** `is_admin`, `setup_mode`, and any copy implying a single operator must configure the install.
5. **Browse gate:** Replace `LibraryScopeGuard` / `HoldingPage` “admin hasn’t finished setup” with a simple redirect to **Settings → Libraries** when `libraries_scoped` is false (or auto-default per item 1 so most users never hit this).
6. **Env/docs:** Drop admin vars from `.env.example` and README; document that library selection is per user in the UI.

**Out of scope:**

- Multi-server / multi-connection picker (still one env-configured connection).
- Sharing one user’s library scope across all app users (remain per `app_user_id`).
- Removing connection configuration from `.env` (server URL stays operator/Docker concern).

**Acceptance criteria:**

- [ ] No `WOF_ADMIN_*` vars required; app starts and runs without them
- [ ] First-time OAuth user sees Browse after sync with all show libraries in scope by default
- [ ] Settings → Libraries works for non–“admin” test user
- [ ] `/setup/admin`, `/setup/libraries`, `AdminSetupPanel`, and `AdminRoute` removed or redirected
- [ ] `PUT .../library-scope` returns 401 without session; 200 for any linked user (not 403 for non-admin)
- [ ] Tests updated: drop admin/setup_mode fixtures; add per-user scope default + settings access tests
- [ ] `SECURITY.md` trust model updated (no admin env gate)

**Notes:**

- Today `ensure_libraries_cached` sets `in_scope` only when `connection.library_allowlist_native_ids` or `WOF_SCOPED_LIBRARY_IDS` is set — that is the main backend change for defaults.
- `SettingsLibrariesPage` copy says “everyone in your household” if scope is per-user; revise to “your libraries” unless product later moves to shared install scope.
- Deprecate `connection.library_allowlist_native_ids` admin PUT path or repurpose as optional env-only bootstrap, not UI-driven admin flow.

---

## UX — Playlist editor

### BL-01: "Don't ask again" on remove-from-playlist confirmation

**Added:** 2026-05-25  
**Target:** Phase 8 (polish) or post-v0.1.0 patch  
**Component:** `RemoveFromPlaylistDialog`, `PlaylistMemberTile`, playlist edit surfaces (`TwoPanePicker`, `PlaylistMembersPanel`, `PlaylistForm`)

**User story:** As an operator editing a playlist, I want to skip the remove confirmation after opting in once, so bulk cleanup in a single edit session is faster — without losing the safety net on my next visit.

**Behavior:**

1. `RemoveFromPlaylistDialog` gains a **"Don't ask again"** checkbox (unchecked by default).
2. When the user confirms remove **with the box checked**, subsequent removes in the **same edit session** call `onRemove` immediately — no dialog.
3. The skip flag is **session-scoped to the current playlist edit** (in-memory React state, not localStorage).
4. **Reset** the flag when either:
   - User clicks **Save playlist** (successful save), or
   - User navigates away from the playlist edit/detail page (unmount / route change), including **Cancel** if it leaves the page.

**Out of scope:**

- Persisting preference across browser sessions
- Applying to playlist delete (whole playlist) or other destructive actions

**Acceptance criteria:**

- [ ] First remove in a session still shows confirmation unless previously opted in
- [ ] Checked "Don't ask again" → next removes in same session are immediate
- [ ] Save playlist → next remove shows confirmation again
- [ ] Navigate to Library / another route → next visit shows confirmation again
- [ ] Vitest: dialog checkbox toggles skip; parent state resets on simulated save/unmount

**Notes:** State should live at the playlist edit container (`PlaylistForm` / page level), passed down to `PlaylistMemberTile` or a small hook — not per-tile isolated state.

---

## Template (for future items)

```markdown
### BL-XX: Title

**Added:** YYYY-MM-DD  
**Target:** Phase N or post-release  
**Component:** paths

**User story:** …

**Behavior:** …

**Acceptance criteria:** …
```
