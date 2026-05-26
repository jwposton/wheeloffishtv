# Backlog — Wheel of Fish TV

Deferred work not scheduled in the current phase. Pull items into a phase plan when ready.

**Last updated:** 2026-05-25

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
