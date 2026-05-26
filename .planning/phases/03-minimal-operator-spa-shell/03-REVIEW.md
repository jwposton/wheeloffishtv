---
phase: 03-minimal-operator-spa-shell
reviewed: 2026-05-25T12:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - backend/src/wheeloffish/api/routes/catalog.py
  - backend/src/wheeloffish/core/auth.py
  - backend/src/wheeloffish/core/media_artwork.py
  - backend/src/wheeloffish/integrations/plex/client.py
findings:
  critical: 2
  warning: 4
  info: 0
  total: 6
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-05-25T12:00:00Z  
**Depth:** standard  
**Files Reviewed:** 4  
**Status:** issues_found

## Summary

Reviewed plan 08 gap-closure changes: admin-token fallback for artwork/resume, cached `ratingKey` optimization, concurrent resume fetches, and artwork URL rewriting. Core fallback logic is sound when Plex returns `401` or artwork `not_found`, but error-mapping gaps leave resume fallback incomplete, and the artwork path guard is bypassable. `auth.py` and `media_artwork.py` are small and mostly correct; main risk is in cross-layer error handling and proxy authorization.

## Critical Issues

### CR-01: Path traversal bypasses `/library/` guard

**File:** `backend/src/wheeloffish/integrations/plex/client.py:174-177`  
**Issue:** `fetch_artwork` only checks `path.startswith("/library/")`. Paths like `/library/metadata/../../../identity` pass the guard but httpx normalizes `..` segments, allowing requests outside the intended library namespace on the configured Plex host.  
**Fix:**
```python
from urllib.parse import urlparse

async def fetch_artwork(self, path: str) -> tuple[bytes, str]:
    if ".." in path or not path.startswith("/library/"):
        raise ProviderError("invalid_path")
    normalized = urlparse(path).path
    if not normalized.startswith("/library/"):
        raise ProviderError("invalid_path")
    url = f"{self.base_url}{normalized}"
    ...
```

### CR-02: Resume admin fallback misses most Plex HTTP errors

**File:** `backend/src/wheeloffish/api/routes/catalog.py:144-146`, `backend/src/wheeloffish/integrations/plex/client.py:67-70`  
**Issue:** `_provider_access_denied` only treats `ProviderUnauthorized` and the exact string `"not_found"` as retriable. `_request` raises `ProviderError("Plex API error: 404")` (and other status codes) for episode/metadata calls, so resume fallback never runs when Plex returns 403/404 instead of 401 — a common pattern for restricted home/managed users. Artwork uses `"not_found"`; resume paths do not.  
**Fix:** Normalize status handling in `_request` (map 401 → `ProviderUnauthorized`, 403/404 → a shared retriable code) or broaden `_provider_access_denied` to inspect `err.code`/status instead of `str(err) == "not_found"`.

## Warnings

### WR-01: Guid resolution bypasses fallback when `ratingKey` absent

**File:** `backend/src/wheeloffish/integrations/plex/mappers.py:88-92`, `backend/src/wheeloffish/api/routes/catalog.py:230-248`  
**Issue:** `resolve_guid_to_rating_key` calls `response.raise_for_status()` and raises `ValueError` on empty results. These are not `ProviderError`, so `_fetch_resume_with_fallback` never catches them. Series without cached `provider_metadata["ratingKey"]` still fail resume for non-admin users despite the admin-fallback intent.  
**Fix:** Wrap guid resolution in `PlexProvider._rating_key_for_series` and map HTTP/auth failures to `ProviderUnauthorized` / retriable `ProviderError`, consistent with `_request`.

### WR-02: Absolute artwork URLs bypass the token proxy

**File:** `backend/src/wheeloffish/core/media_artwork.py:8-9`  
**Issue:** `public_artwork_url` returns absolute `http(s)://` URLs unchanged. If sync stores full Plex URLs (possible from provider metadata), non-admin clients load posters directly from Plex and hit the same auth failure the proxy was added to fix.  
**Fix:** Always rewrite to the same-origin proxy for Plex-relative paths; for absolute Plex URLs, extract the path component and proxy it, or normalize at sync time to relative paths only.

### WR-03: Artwork proxy has no catalog binding with admin fallback

**File:** `backend/src/wheeloffish/api/routes/catalog.py:354-389`, `148-167`  
**Issue:** Any authenticated user with a media link can request any `path` starting with `/library/`. On user-token failure, admin credentials fetch the resource. There is no check that the path belongs to a cached in-scope series shown to that user. Acceptable for a shared home library, but enables enumeration of admin-visible metadata IDs.  
**Fix:** Optionally validate `path` against cached `thumb_url` values for in-scope series, or document this as an explicit trust model.

### WR-04: Episodes endpoint lacks resume parity

**File:** `backend/src/wheeloffish/api/routes/catalog.py:438-455`  
**Issue:** `get_series_episodes` calls `provider.list_episodes(series_id)` without cached `rating_key` or admin-token fallback. Non-admin users may still get 422 on series detail episode lists while resume works after plan 08 changes.  
**Fix:** Reuse `_cached_rating_key`, `_fetch_resume_with_fallback`-style fallback, or a shared helper for provider calls that need admin escalation.

---

_Reviewed: 2026-05-25T12:00:00Z_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: standard_
