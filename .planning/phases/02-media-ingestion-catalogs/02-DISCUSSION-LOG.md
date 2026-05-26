# Phase 2: Media ingestion & catalogs - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 2-Media ingestion & catalogs
**Areas discussed:** Plex-first vs Jellyfin parity, Connection & credential model, Resume pointer semantics, Catalog cache & sync strategy, Provider interface & DTO shape

---

## Plex-first vs Jellyfin parity

| Option | Description | Selected |
|--------|-------------|----------|
| Plex complete, Jellyfin stub | Full Plex; Jellyfin NotImplementedError | |
| Plex complete, Jellyfin read-only parity | Both list/browse; Jellyfin no write-back | |
| Full parity day one | Both connectors equally complete | ✓ |
| You decide | Agent picks | |

**Q2 — Gap handling when APIs differ:**

| Option | Description | Selected |
|--------|-------------|----------|
| Strict parity | Identical DTOs; unsupported flags | |
| Pragmatic parity | Same shape; nullable fields; document per provider | ✓ |
| Plex canonical | Plex DTO is source of truth | |
| You decide | Agent picks | |

**Q3 — Testing:**

| Option | Description | Selected |
|--------|-------------|----------|
| Live-server integration tests (optional) | Mocks baseline + optional live CI | |
| Recorded fixtures only | Sanitized snapshots in CI | |
| Both | Mocks + fixtures + manual live UAT | ✓ |
| You decide | Agent picks | |

**Q4 — API exposure:**

| Option | Description | Selected |
|--------|-------------|----------|
| Internal only | Protocol only; no HTTP routes | |
| Debug/admin API | Minimal curl-friendly routes | |
| Full catalog API | REST for Phase 3 SPA | ✓ |
| You decide | Agent picks | |

---

## Connection & credential model

**Q1 — Connection count:**

| Option | Description | Selected |
|--------|-------------|----------|
| One active connection | Plex OR Jellyfin only | |
| One of each | Max one Plex + one Jellyfin | ✓ (refined) |
| Multiple per type | Home + vacation servers | |
| You decide | Agent picks | |

**Notes:** Refined — neither provider required; `WOF_ENABLED_PROVIDERS` env gates which types users may configure.

**Q2 — DB vs vault split:**

| Option | Description | Selected |
|--------|-------------|----------|
| Vault-heavy | All sensitive fields in vault | |
| Split | DB config; vault tokens only | ✓ |
| DB encrypted columns | Column-level encryption | |
| You decide | Agent picks | |

**Q3 — Validation flow:**

| Option | Description | Selected |
|--------|-------------|----------|
| Test-then-save | Ping provider before persist | ✓ |
| Save-then-test | Async pending/failed states | |
| Save without test | Errors surface later | |
| You decide | Agent picks | |

**Q4 — Credential entry:**

| Option | Description | Selected |
|--------|-------------|----------|
| Manual token only | Copy-paste token/key | |
| Manual + Plex PIN | PIN for Plex; manual Jellyfin | |
| Full OAuth for both | Plex OAuth + Jellyfin auth flow | ✓ |
| Manual now, OAuth deferred | Token only; schema OAuth-ready | |

**Notes:** User wants OAuth working early so Phase 3 is not blocked on credential UX.

---

## Resume pointer semantics

**Q1 — Resume meaning:**

| Option | Description | Selected |
|--------|-------------|----------|
| Earliest unfinished | Walk order; ignore On Deck | |
| Provider up next | Trust On Deck / Next Up | |
| Hybrid | Earliest unfinished unless provider ahead | ✓ |
| Earliest unfinished, season-scoped | Don't jump seasons | |

**Q2 — Partial vs complete thresholds:**

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed threshold | 5%/95% same for both | |
| Provider-native | Map flags directly | |
| Fixed + provider override | 5%/95% + viewCount/Played override | ✓ |
| Configurable per install | Env override | |

**Q3 — Specials ordering:**

| Option | Description | Selected |
|--------|-------------|----------|
| Include in sequence | S00 in provider order | |
| Exclude by default | Main seasons only | |
| After current season | Specials after season finale | ✓ |
| Provider order only | No reinterpretation | |

**Q4 — Multi-viewer watch state:**

| Option | Description | Selected |
|--------|-------------|----------|
| Connection owner only | Single watch history | |
| Per-app-user binding | Each user links own media account | ✓ |
| Household aggregate | Slowest watcher sets pace | |
| Most-progress | Furthest ahead wins | |

**Notes:** User clarified each Plex user has own watch history, settings, and playlists.

---

## Catalog cache & sync strategy

**Q1 — Cache depth (refined from Option 4 advice):**

| Option | Description | Selected |
|--------|-------------|----------|
| Full catalog cache | Everything in SQLite | |
| Watch state + show list | Episodes live | |
| Minimal cache | Live API on demand | |
| Lazy episodes | User refinement | ✓ (refined) |

**Notes:** User refinement — show metadata only for browse/add-to-playlist; episode + watch data fetched fresh at scheduled playlist rebuild, not cached (watch state changes between refreshes).

**Q2 — Show metadata refresh triggers:**

| Option | Description | Selected |
|--------|-------------|----------|
| Connect + manual only | No login sync | |
| Daily + manual | Nightly show sync | |
| Daily + stale on browse | TTL check | |
| Connect + login + manual | OAuth, login, manual refresh | ✓ |

**Q3 — Scale / browse:**

| Option | Description | Selected |
|--------|-------------|----------|
| Full list client search | All shows to SPA | |
| Server paging + search | API pages cached data | |
| Server paging, lazy sync | Chunked background sync | ✓ |
| Library-scoped browse | Pick library first | |

**Notes:** Combined with install-level library scoping (admin selects libraries at setup).

**Q4 — Sync UX during login:**

| Option | Description | Selected |
|--------|-------------|----------|
| Block until done | Login waits for sync | |
| Immediate + stale + banner | Fast login; background refresh | ✓ |
| Immediate + empty | Spinner until first chunk | |
| Block with progress | Login waits with progress UI | |

---

## Provider interface & DTO shape

**Q1 — Stable ID scheme:**

| Option | Description | Selected |
|--------|-------------|----------|
| Provider-prefixed native IDs | plex://show/123 | |
| Internal UUID + mapping | UUID table | |
| Composite string keys | connection:provider:native_id | ✓ |
| Provider-native only | No normalization | |

**Notes:** Use stable Plex GUIDs where available; resolve ratingKeys at API-call time.

**Q2 — Core DTOs:**

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal browse set | Library, Series, Episode | |
| Browse + watch snapshot | Episode includes watch fields at fetch | ✓ |
| Browse + resume cursor | Provider returns ResumeCursor | |
| Full catalog graph | Nested seasons/groups | |

**Notes:** ResumeCursor computed by domain service, not provider.

**Q3 — Multipart hints (refined):**

| Option | Description | Selected |
|--------|-------------|----------|
| Optional fields on Episode | part_index, group_id when provider has them | ✓ |
| Defer entirely | Phase 4 heuristics | |
| Separate MultipartGroup DTO | Explicit groupings | |
| Episode links only | continues_from/to refs | |

**Notes:** User confirmed multipart fields on Episode DTO only when valid native provider API fields exist; no Phase 2 heuristics.

**Q4 — Phase 2 implement vs define:**

| Option | Description | Selected |
|--------|-------------|----------|
| Browse only | fetch_episodes stubbed | |
| Browse + episode probe | Live episodes for UAT | |
| Browse + resume preview | Episodes + ResumeCursor endpoint | ✓ |
| Full provider surface | All methods; consumers later | |

---

## Claude's Discretion

- OAuth redirect URLs, chunk sizes, paging defaults, exact error payload schema, Plex GUID resolution internals.

## Deferred Ideas

- Multipart adjacency enforcement — Phase 4
- Heuristic multipart when provider lacks fields — Phase 4
- Nightly show-metadata sync — login + manual sufficient
- Episode SQLite cache — rejected by user
- Playlist build, scheduler, SPA — later phases
