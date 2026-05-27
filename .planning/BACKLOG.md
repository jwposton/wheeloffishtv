# Backlog — Wheel of Fish TV

Deferred work not scheduled in the current phase. Pull items into a phase plan when ready.

**Last updated:** 2026-05-26

---

## Completed (shipped post–v0.1.0 UAT)

### BL-02: Per-user library settings (removed admin RBAC) — 2026-05-26

Delivered: no `WOF_ADMIN_*`; **Settings → Libraries** for any linked user; `PUT /api/v1/connections/{id}/library-scope`; first-sync default all TV libraries in scope. See [CHANGELOG.md](../CHANGELOG.md) and [README.md](../README.md).

### BL-01: "Don't ask again" on remove-from-playlist confirmation — 2026-05-26

Delivered: session-scoped skip in playlist edit/detail; resets on save or navigation. See CHANGELOG.

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
