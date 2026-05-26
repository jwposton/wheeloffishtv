# Debug: Non-admin broken poster images

**UAT Test:** 5  
**Symptom:** Admin sees posters; non-admin sees broken images on browse grid.

## Root Cause

Artwork proxy uses per-user Plex OAuth token. Thumb paths cached during admin sync use rating-key URLs that home/managed users cannot fetch.

## Fix Direction

Admin-token fallback in `get_connection_artwork` when user token fails.
