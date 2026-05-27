# Debug: Holding page vs setup mode

**Status:** Superseded 2026-05-26 (BL-02).

`HoldingPage`, setup mode, and `WOF_ADMIN_*` were removed. When `libraries_scoped` is false, `LibraryScopeGuard` redirects to **Settings → Libraries**. First catalog sync defaults all TV libraries in scope for new users.

Historical note: earlier UAT conflated `setup_mode` (admin env unset) with `libraries_scoped=false`. Re-test unscoped behavior by clearing all in-scope flags in **Settings → Libraries**, not by omitting admin env vars.
