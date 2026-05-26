# Debug: Resume preview failure

**UAT Test:** 6, 7  
**Symptom:** Long wait then "Could not load resume data for this series."

## Root Cause

Resume endpoint makes redundant guid→ratingKey Plex lookups; failures on `/library/all?guid=` or episode fetch return 422. Cached `ratingKey` not used.

## Fix Direction

Use cached ratingKey, parallelize fetches, admin-token fallback for home users.
