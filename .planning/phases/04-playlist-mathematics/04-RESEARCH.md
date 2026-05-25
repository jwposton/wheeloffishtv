# Phase 4: Playlist mathematics - Research

**Researched:** 2026-05-25
**Domain:** Pure-domain playlist generation — ordered serial picks from resume, disordered seeded feathers, multipart adjacency, completion policies
**Confidence:** HIGH (resume/multipart inputs verified in codebase); MEDIUM (slot-allocation semantics — no 04-CONTEXT.md yet)

<user_constraints>
## User Constraints (from PROJECT / REQUIREMENTS / ROADMAP — no 04-CONTEXT.md yet)

> Phase 4 has not run `/gsd-discuss-phase`. Constraints below are locked from project docs and inherited Phase 2 resume semantics. Planner should treat Phase 2 D-10–D-13, D-21 as hard dependencies.

### Locked Decisions (inherited + roadmap)

- **Phase boundary:** Pure algorithm + unit/property tests only — no DB migrations, REST CRUD, scheduler, SPA, or WheelOfFish admin (Phases 5–6).
- **Resume semantics (Phase 2 D-10–D-13):** Hybrid resume via existing `ResumeService` — earliest unfinished unless provider on-deck is ahead with no unfinished gaps; watch thresholds D-11; specials ordering D-12; per-user watch state keyed `(app_user, connection, series)` at rebuild time (Phase 5 fetches live episodes).
- **Episode inputs (Phase 2 D-20–D-21):** Builder consumes in-memory `list[Episode]` + optional on-deck `Episode | None` per series — same shape as catalog `/episodes` and `/resume` routes. Multipart uses native `part_index` / `multipart_group_id` when present; no provider HTTP in Phase 4 tests.
- **PLT-02…PLT-06:** Implement generator for `N` episodes per playlist config, per-row `ordered` vs `disordered`, serial forward from resume for ordered rows, completion policies `remove` | `restart` | `disordered`.
- **SCH-02 (algorithm only):** Multipart sibling parts adjacent in continuity order within a refresh output when any part qualifies on an **ordered** row — enforcement logic lives here; persistence/scheduling in Phase 5.
- **Determinism:** ROADMAP success criterion — golden-vector tests + day-key seed stability for disordered stochastic picks.
- **ROADMAP Mode:** MVP vertical slices with test-first proofs.

### Claude's Discretion (research recommendations — confirm in discuss/plan if needed)

- Default **completion event** = `series_complete` (all episodes `COMPLETE` per `classify_watch`); optional `season_complete` enum value for future UX.
- **Slot allocation:** uniform random assignment of `N` slots across active rows (with replacement), materialized left-to-right using seeded `random.Random`.
- **Disordered pool:** all episodes in series (including completed) unless row removed by policy — true “random feather” chaos.
- **Multipart expansion:** one slot consumes one allocation but may emit multiple adjacent episodes (block expansion).
- **Short output:** if rows exhaust before `N` slots filled, emit fewer than `N` and surface `slots_unfilled` in build result (do not silently backfill from other rows without explicit rule).
- **Heuristic multipart fallback** when `multipart_group_id` is null: defer to optional Wave 1.5 only if golden vectors need it — prefer native fields first per D-21.
- Domain module layout (`core/playlist/` vs flat `core/playlist_builder.py`), exact day-key string format, Hypothesis vs stdlib-only property tests.

### Deferred Ideas (OUT OF SCOPE — Phase 4)

- Playlist DB persistence, Alembic migrations, rebuild job runner (Phase 5)
- REST playlist CRUD, manual rebuild API, job status (Phase 5 + WEB-01)
- WheelOfFish global playlist + admin RBAC (Phase 6)
- SPA playlist authoring UI (Phase 5/7)
- Live MediaProvider fetches inside builder (Phase 5 orchestration passes inputs)
- Plex/Jellyfin playlist export / push API (later)
- Episode SQLite cache (explicitly rejected Phase 2)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PLT-01 | Multiple named playlists | In-memory `Playlist` domain model with `id`, `name`, `rows` — persistence deferred Phase 5 |
| PLT-02 | Episode count `N` per rebuild | `Playlist.episode_count: int` drives slot allocation loop |
| PLT-03 | Add/remove series to playlist | `PlaylistSeriesRow.series_id` membership list on `Playlist.rows` — CRUD deferred |
| PLT-04 | Per playlist×series `ordered` / `disordered` | `RowMode` enum on `PlaylistSeriesRow` |
| PLT-05 | Ordered rows serial forward from resume | `ResumeService.compute()` + forward walk on `order_episodes()` list |
| PLT-06 | Completion event + policy (`remove`/`restart`/`disordered`) | `CompletionEvent` + `CompletionPolicy` enums; `evaluate_completion()` + `apply_policy()` pure functions |
| SCH-02 | Multipart adjacency in ordered output | `expand_multipart_block()` groups by `multipart_group_id`, sorts by `part_index`, inserts contiguously |
</phase_requirements>

## Summary

Phase 4 builds a **pure, testable playlist generator** in `backend/src/wheeloffish/core/` that turns a configured `Playlist` plus per-series live episode snapshots into an ordered list of `BuiltEpisode` entries. Phase 2 already delivers the hard resume math (`ResumeService`, `order_episodes`, `classify_watch`) and multipart metadata on `Episode` (`part_index`, `multipart_group_id` from Plex/Jellyfin mappers). Phase 4 composes these into a **two-phase build**: (1) evaluate completion policies and derive effective row modes/cursors, (2) allocate `N` pseudo-random **slots** across active rows using a **day-key-seeded RNG**, then materialize each slot — ordered rows advance a serial cursor (with multipart block expansion), disordered rows pick a random episode from the series pool without replacement within the refresh.

The generator is **HTTP- and DB-free**. Phase 5 will fetch episodes via existing catalog/provider paths, construct `SeriesRebuildInput` bundles, call `PlaylistBuilder.build()`, and persist outputs. SCH-02 adjacency is proven here with golden vectors and optional Hypothesis property tests; Phase 5 only orchestrates timing and storage.

**Primary recommendation:** Implement `PlaylistBuilder` as a small pipeline — `completion` → `multipart` → `ordered_cursor` → `disordered_picker` → `slot_allocator` — with golden-vector fixtures mirroring `test_resume_service.py` patterns and day-key seeds verified by identical outputs on repeated builds.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Resume / watch classification | `core/resume.py` (existing) | — | Already domain-pure; builder imports, does not duplicate |
| Multipart grouping & adjacency | `core/playlist/multipart.py` (new) | `domain/dto.Episode` fields | Pure list transforms on in-memory episodes |
| Completion detection & policy | `core/playlist/completion.py` (new) | `classify_watch` / `order_episodes` | Business rules before slot allocation |
| Ordered serial picker | `core/playlist/ordered.py` (new) | `ResumeService` | Cursor state per row during build |
| Disordered feather picker | `core/playlist/disordered.py` (new) | Seeded `random.Random` | Stochastic but deterministic per day-key |
| Slot allocation & orchestration | `core/playlist/builder.py` (new) | All submodules | Single entry `PlaylistBuilder.build()` |
| Episode/watch data fetch | — (Phase 5) | `MediaProvider` + catalog routes | Phase 4 accepts pre-fetched inputs only |
| Playlist CRUD / persistence | — (Phase 5) | DB models | Out of scope |
| Daily scheduler | — (Phase 5) | APScheduler/worker | Out of scope |
| UI / API exposure | — (Phase 5+) | FastAPI routes | Out of scope |

## Standard Stack

### Core (existing — no new runtime deps required)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | ≥3.12 | Domain implementation | Project baseline (`pyproject.toml`) |
| Pydantic v2 | (via FastAPI dep) | Playlist domain models | Matches `domain/dto.py` pattern |
| pytest | ≥8.0 | Golden-vector tests | 108 tests already collected |
| stdlib `random.Random` | — | Day-key seeded disordered picks | Deterministic without extra deps |

### Supporting (optional dev)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `hypothesis` | 6.152.9 on PyPI `[ASSUMED]` | Property tests (adjacency, seed stability, no duplicate disordered picks) | Add in Wave 0/6 if planner wants generative coverage |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Uniform slot RNG | Round-robin row rotation | Less “wheel of fish” chaos; rejected for product promise |
| `random.Random` | `numpy.random.Generator` | Heavier dep for simple shuffle |
| Golden vectors only | Hypothesis-only | Harder to debug regressions; use both |
| Series-complete default | Season-complete default | REQ allows season granularity — ship series first |

**Installation (optional):**
```bash
cd backend && uv add --dev hypothesis
```

**Version verification:** `hypothesis` 6.152.9 via `pip index versions hypothesis` (2026-05-25). Stdlib `random` requires no install.

## Package Legitimacy Audit

> slopcheck unavailable at research time — optional package tagged `[ASSUMED]`.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| hypothesis | PyPI | ~10+ yrs | very high | github.com/HypothesisWorks/hypothesis | unavailable | Approved with `[ASSUMED]` — planner adds `checkpoint:human-verify` before install |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*If Hypothesis is skipped, property invariants can be covered with parametrized pytest + fixed seeds only.*

## Architecture Patterns

### System Architecture Diagram

```
Phase 5 orchestrator (future)
    │  live Episode[] + on_deck per series_id
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PlaylistBuilder.build(playlist, inputs, day_key)             │
│  1. completion.evaluate → row eligibility + policy effects   │
│  2. allocate N slots → [row_id, row_id, ...]  (seeded)       │
│  3. for each slot:                                           │
│       ordered    → ordered.next_block(cursor, multipart)     │
│       disordered → disordered.pick_episode(pool, rng)         │
│  4. flatten blocks → list[BuiltEpisode]                      │
└─────────────────────────────────────────────────────────────┘
    │  reuses
    ▼
┌──────────────────┐     ┌─────────────────────┐
│ ResumeService    │     │ order_episodes       │
│ classify_watch   │     │ Episode.multipart_*  │
└──────────────────┘     └─────────────────────┘
    ▲
    │  same inputs as
┌─────────────────────────────────────────────────────────────┐
│ catalog.py GET …/episodes  +  GET …/resume  (Phase 2)       │
└─────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
backend/src/wheeloffish/
├── domain/
│   ├── dto.py                    # existing Episode, ResumeCursor
│   └── playlist.py               # NEW: Playlist, PlaylistSeriesRow, BuiltEpisode, enums
├── core/
│   ├── resume.py                 # existing — import, do not fork
│   └── playlist/
│       ├── __init__.py
│       ├── builder.py            # PlaylistBuilder orchestrator
│       ├── completion.py         # completion events + policies
│       ├── multipart.py          # group expansion + adjacency helpers
│       ├── ordered.py            # serial cursor + forward picks
│       └── disordered.py         # seeded pool sampling
backend/tests/
├── unit/
│   ├── test_resume_service.py    # existing golden pattern
│   ├── test_multipart.py         # NEW
│   ├── test_completion_policies.py
│   ├── test_ordered_picker.py
│   ├── test_disordered_picker.py
│   ├── test_playlist_builder.py  # end-to-end golden vectors
│   └── fixtures/
│       └── playlist_vectors.py   # shared episode factories
```

### Pattern 1: In-memory domain models (PLT-01–04)

**What:** Pydantic models describing playlist config passed into builder — no SQLAlchemy yet.

**When to use:** All Phase 4 tests and Phase 5 orchestrator input contract.

```python
# domain/playlist.py — illustrative; planner finalizes names
from enum import StrEnum
from pydantic import BaseModel, Field

class RowMode(StrEnum):
    ORDERED = "ordered"
    DISORDERED = "disordered"

class CompletionPolicy(StrEnum):
    REMOVE = "remove"
    RESTART = "restart"
    DISORDERED = "disordered"

class CompletionEvent(StrEnum):
    SERIES_COMPLETE = "series_complete"
    SEASON_COMPLETE = "season_complete"

class PlaylistSeriesRow(BaseModel):
    series_id: str
    mode: RowMode = RowMode.ORDERED
    completion_policy: CompletionPolicy = CompletionPolicy.REMOVE
    completion_event: CompletionEvent = CompletionEvent.SERIES_COMPLETE

class Playlist(BaseModel):
    id: str
    name: str
    episode_count: int = Field(ge=1)
    rows: list[PlaylistSeriesRow]

class SeriesRebuildInput(BaseModel):
    series_id: str
    episodes: list[Episode]
    on_deck: Episode | None = None

class BuiltEpisode(BaseModel):
    episode: Episode
    series_id: str
    row_mode: RowMode
    slot_index: int

class RowBuildOutcome(BaseModel):
    series_id: str
    effective_mode: RowMode
    excluded: bool = False
    policy_applied: CompletionPolicy | None = None

class PlaylistBuildResult(BaseModel):
    episodes: list[BuiltEpisode]
    row_outcomes: list[RowBuildOutcome]
    day_key: str
    slots_requested: int
    slots_filled: int
```

### Pattern 2: Day-key seeded slot allocation

**What:** Derive stable RNG from `(playlist_id, day_key)` so disordered picks and slot row choices repeat for the same calendar rebuild.

**When to use:** Every `PlaylistBuilder.build()` call; tests pass explicit `day_key="2026-05-25"`.

```python
import hashlib
import random

def make_build_rng(playlist_id: str, day_key: str) -> random.Random:
    seed_material = f"{playlist_id}:{day_key}".encode()
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    return random.Random(seed)

def allocate_slots(active_row_ids: list[str], n: int, rng: random.Random) -> list[str]:
    if not active_row_ids:
        return []
    return [rng.choice(active_row_ids) for _ in range(n)]
```

`day_key` format recommendation: ISO date `YYYY-MM-DD` in operator timezone — Phase 5 passes computed value; Phase 4 tests use fixed strings.

### Pattern 3: Ordered serial forward from resume (PLT-05)

**What:** For each ordered row, compute start index once via `ResumeService`, then walk `order_episodes()` forward, expanding multipart blocks.

```python
from wheeloffish.core.resume import ResumeService, order_episodes

def start_index(series_id: str, episodes: list[Episode], on_deck: Episode | None) -> int:
    ordered = order_episodes(episodes)
    cursor = ResumeService().compute(series_id, episodes, on_deck)
    if cursor.series_complete:
        return len(ordered)  # exhausted
    assert cursor.episode_id
    return next(i for i, ep in enumerate(ordered) if ep.id == cursor.episode_id)

def next_ordered_block(ordered: list[Episode], index: int, episodes_by_id: dict) -> tuple[list[Episode], int]:
    if index >= len(ordered):
        return [], index
    anchor = ordered[index]
    block = expand_multipart_block(anchor, episodes_by_id)
    return block, index + len(block)  # advance by logical steps in ordered list
```

**Partial episodes:** Resume cursor already points at partial installment; block includes that episode (and multipart siblings per Pattern 4).

### Pattern 4: Multipart adjacency (SCH-02 preview)

**What:** When any episode in a multipart group is selected on an **ordered** row, emit all episodes sharing `multipart_group_id`, sorted by `part_index` (nulls last), contiguously. One slot → one block.

**Rules:**
1. **Group key:** `multipart_group_id` when non-null (Plex `multipartGroupId`, Jellyfin `MultipartGroupId`) `[VERIFIED: codebase mappers]`.
2. **Order within block:** ascending `part_index`; tie-break by `episode.id` for stability.
3. **Anchor resolution:** If resume points at part 3 of 3, block is parts 1–3 if all share group (include unwatched leading parts) `[ASSUMED]` — matches binge continuity expectation; confirm in discuss.
4. **Disordered rows:** Multipart adjacency **not required** by SCH-02 (ordered contexts only); disordered picks single episodes unless product later extends rule.
5. **Missing metadata:** Episodes with null `multipart_group_id` emit as singleton blocks. Optional heuristic (same `season_index`, `episode_index`, consecutive `part_index`) deferred unless vectors require it (Phase 2 D-21).

```python
def expand_multipart_block(anchor: Episode, episodes_by_id: dict[str, Episode]) -> list[Episode]:
    if not anchor.multipart_group_id:
        return [anchor]
    group = [
        ep for ep in episodes_by_id.values()
        if ep.multipart_group_id == anchor.multipart_group_id
    ]
    group.sort(key=lambda e: (e.part_index is None, e.part_index or 0, e.id))
    return group
```

### Pattern 5: Completion events and policies (PLT-06)

| Event | Detect when | Notes |
|-------|-------------|-------|
| `series_complete` (default) | `ResumeService.compute(...).series_complete is True` | All episodes COMPLETE per D-11 |
| `season_complete` | All episodes in highest unfinished season COMPLETE | Scan `order_episodes` groups by `season_index` |

| Policy | Behavior on next build |
|--------|------------------------|
| `remove` | Row excluded from active pool (`excluded=True` in outcome) |
| `restart` | Row stays `ordered`; cursor forced to index 0 of `order_episodes` (S1E1 after specials ordering) |
| `disordered` | Row stays in pool with `effective_mode=DISORDERED` regardless of configured mode |

Policy applies **at start of build** when completion event fires; Phase 5 may persist mode changes — Phase 4 returns `RowBuildOutcome` for orchestrator to apply.

### Anti-Patterns to Avoid

- **Reimplementing resume math in builder:** Duplicates D-10 hybrid rule and breaks parity with `/resume` endpoint.
- **Global unseeded `random`:** Breaks day-key stability ROADMAP criterion.
- **Splitting multipart blocks across non-adjacent slots:** Violates SCH-02 for ordered rows.
- **Fetching episodes inside builder:** Couples pure math to httpx; untestable without fixtures.
- **DB models in Phase 4:** Scope creep — keep config as Pydantic inputs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Resume pointer | Custom “up next” scan | `ResumeService` + `order_episodes` | Phase 2 golden vectors already prove behavior |
| Watch complete vs partial | Ad-hoc percent checks | `classify_watch` | Single threshold source (D-11) |
| Episode ordering | Season/special sort | `order_episodes` | D-12 specials-after-finale rule |
| Deterministic shuffle | Custom LCG | `random.Random` with hashed seed | Stdlib, auditable, test-friendly |
| Multipart identity | Title/SxxExx regex (initially) | Native `multipart_group_id` | D-21; heuristics only as fallback |
| Property testing framework | Custom example generator | Hypothesis `[ASSUMED]` or parametrized pytest | Adjacency invariants need many permutations |

**Key insight:** Phase 4 is composition of proven Phase 2 primitives plus slot algebra — the risk is policy/slot edge cases, not resume discovery.

## Common Pitfalls

### Pitfall 1: Resume / builder drift
**What goes wrong:** `/resume` preview disagrees with playlist ordered picks.
**Why it happens:** Builder reimplements ordering or on-deck logic.
**How to avoid:** Single code path — `ResumeService` + `order_episodes` only.
**Warning signs:** Golden vector passes in `test_resume_service` but fails in `test_playlist_builder`.

### Pitfall 2: Multipart block split across slots
**What goes wrong:** Part 1 at position 3, part 2 at position 9.
**Why it happens:** Slot materialization picks one part per slot without expansion.
**How to avoid:** `expand_multipart_block` returns full block; advance ordered index by block length in ordered list coordinates.
**Warning signs:** Property test finds same `multipart_group_id` non-contiguous indices.

### Pitfall 3: Day-key instability
**What goes wrong:** Same-day manual rebuilds produce different playlists.
**Why it happens:** Unseeded RNG or timezone-dependent key without documentation.
**How to avoid:** Explicit `day_key` parameter; document ISO date in operator TZ (Phase 5).
**Warning signs:** Repeated `build()` in test with same inputs yields different order.

### Pitfall 4: Disordered with-replacement surprise
**What goes wrong:** Same episode appears twice in one refresh.
**Why it happens:** `rng.choice` on full pool each slot.
**How to avoid:** Per-row pool as mutable set/list; remove picked episode for that refresh (recommended `[ASSUMED]`).
**Warning signs:** User sees duplicate feather same night.

### Pitfall 5: Completion policy applied mid-build
**What goes wrong:** Row removed after partially emitting episodes in same refresh.
**Why it happens:** Interleaved completion checks.
**How to avoid:** Evaluate all completions **before** slot allocation; policies affect **this** build's mode/eligibility consistently.
**Warning signs:** `remove` policy row still contributes slots.

### Pitfall 6: Ordered row exhaust with silent backfill
**What goes wrong:** Builder pulls from unrelated row to fill N.
**Why it happens:** Implicit backfill logic.
**How to avoid:** Return `slots_filled < slots_requested`; Phase 5 surfaces warning in UI.
**Warning signs:** Tests expect exactly N always — document exception.

### Pitfall 7: Specials ordering breaks serial cursor
**What goes wrong:** Ordered pick skips specials or resumes before finale.
**Why it happens:** Cursor index on raw provider order instead of `order_episodes`.
**How to avoid:** All forward walks use `order_episodes` list exclusively.

## Code Examples

### Existing code to reuse

**ResumeService** — hybrid resume (import as-is):

```107:126:backend/src/wheeloffish/core/resume.py
class ResumeService:
    """Domain service for hybrid resume pointer computation (D-10)."""

    def compute(
        self,
        series_id: str,
        episodes: list[Episode],
        on_deck: Episode | None,
    ) -> ResumeCursor:
        """Compute resume cursor using hybrid on-deck rule (D-10)."""
        ordered = order_episodes(episodes)
        earliest = next((e for e in ordered if classify_watch(e) != WatchState.COMPLETE), None)

        if earliest is None:
            return ResumeCursor(series_id=series_id, series_complete=True)

        if on_deck is not None and is_ahead_in_sequence(on_deck, earliest, ordered):
            return _cursor_from_episode(on_deck, source="on_deck", series_id=series_id)

        return _cursor_from_episode(earliest, source="earliest_unfinished", series_id=series_id)
```

**Episode DTO** — multipart fields:

```39:51:backend/src/wheeloffish/domain/dto.py
class Episode(BaseModel):
    id: str
    title: str
    season_index: int
    episode_index: int
    duration_ms: int
    percent_watched: float = Field(ge=0, le=100)
    provider_marked_played: bool = False
    part_index: int | None = None
    multipart_group_id: str | None = None
    is_special: bool = False
    special_for_season: int | None = None
```

**Catalog integration contract** (Phase 5 caller, not Phase 4 implementation):

```199:264:backend/src/wheeloffish/api/routes/catalog.py
async def _fetch_resume_data(
    provider: MediaProvider,
    series_id: str,
    ...
) -> tuple[list[Episode], Episode | None]:
    ...
    return episodes, on_deck

def _resume_cursor(
    series_id: str,
    episodes: list[Episode],
    on_deck: Episode | None,
) -> ResumeCursor:
    ...
    return ResumeService().compute(series_id, episodes, on_deck)
```

### Golden-vector test factory (mirror Phase 2)

```python
# tests/unit/fixtures/playlist_vectors.py
from wheeloffish.domain.dto import Episode

def episode(
    episode_id: str,
    season: int,
    index: int,
    *,
    percent: float = 0.0,
    played: bool = False,
    part_index: int | None = None,
    multipart_group_id: str | None = None,
) -> Episode:
    return Episode(
        id=episode_id,
        title=f"S{season}E{index}",
        season_index=season,
        episode_index=index,
        duration_ms=3_600_000,
        percent_watched=percent,
        provider_marked_played=played,
        part_index=part_index,
        multipart_group_id=multipart_group_id,
    )
```

### Golden-vector scenarios (minimum set)

| Vector | Setup | Assert |
|--------|-------|--------|
| `ordered_single_row` | 1 ordered row, N=3, fresh series 6 eps | Output S1E1,S1E2,S1E3 serially |
| `ordered_resume_partial` | Partial at S1E3 | Starts S1E3,S1E4,… |
| `disordered_seed_stable` | 2 rows, N=10, fixed day_key | Byte-identical episode id list across 2 builds |
| `disordered_seed_changes` | Same config, different day_key | Lists differ (stochastic) |
| `mixed_ordered_disordered` | 2 rows ordered+disordered, N=8 | Ordered segments serial; disordered from pool |
| `multipart_ordered` | 3 parts same group at resume | 3 contiguous ids sorted by part_index |
| `policy_remove` | Series complete + remove | Row absent from output; `excluded=True` |
| `policy_restart` | Series complete + restart | Next build starts S1E1 |
| `policy_disordered` | Series complete + disordered | Row picks random feathers, not serial |
| `on_deck_skip` | Reuse Phase 2 skip vector | Ordered row starts at on-deck episode |

### Property test invariants (Hypothesis or parametrized)

1. **Multipart adjacency (ordered):** For any build output, indices of episodes sharing `multipart_group_id` form a contiguous range.
2. **Part order:** Within a block, `part_index` is non-decreasing.
3. **Seed stability:** `build(playlist, inputs, day_key)` idempotent for same inputs.
4. **Ordered monotonicity:** For a single ordered row in isolation, emitted episode indices in `order_episodes` order are strictly increasing (excluding multipart internal reorder).
5. **Disordered no-replacement:** Same series does not repeat same episode id within one build `[ASSUMED]`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Resume in provider | `ResumeService` domain | Phase 2 | Builder must reuse, not re-fetch semantics |
| Multipart heuristics in ingestion | Native `multipart_group_id` on Episode | Phase 2 D-21 | Phase 4 groups on mapped fields first |
| Playlist math + persistence together | Phase 4 pure / Phase 5 orchestration | ROADMAP v1 | Enables exhaustive unit tests without DB |

**Deprecated/outdated:**
- Building playlist logic inside FastAPI routes — keep in `core/playlist/`

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Uniform slot allocation across active rows | Pattern 2 | Some shows over/under-represented |
| A2 | Disordered pool = all episodes; no replacement within refresh | Pattern 3 / Pitfall 4 | Duplicate feathers or overly narrow pool |
| A3 | Multipart block includes all group members when anchor selected | Pattern 4 | User misses part 1 of split episode |
| A4 | Default completion event = series_complete | Pattern 5 | Season-finale policies wrong |
| A5 | Short playlist when rows exhaust (no backfill) | Pitfall 6 | UI expects exactly N always |
| A6 | SCH-02 adjacency only for ordered rows | Pattern 4 | Disordered multipart may split |
| A7 | `day_key` = ISO date string | Pattern 2 | Timezone bugs in Phase 5 |
| A8 | Hypothesis optional dev dependency | Standard Stack | Skip if team prefers vectors only |

## Open Questions

1. **Multipart anchor includes prior parts?**
   - What we know: SCH-02 requires sibling adjacency and continuity order.
   - What's unclear: Whether picking up at part 2 should prepend part 1 if unwatched.
   - Recommendation: Include all parts in group sorted by `part_index` (A3); golden-vector proof in Wave 1.

2. **Season vs series completion default for PLT-06**
   - What we know: REQ says "finalized in PLAN."
   - Recommendation: Implement both enums; default `series_complete`; season logic in same module.

3. **Does N count multipart parts or logical slots?**
   - Recommendation: **Slots** — one allocation may expand to multiple output episodes (ROADMAP adjacency over strict N).

4. **When `/gsd-discuss-phase` runs, will PLT-01/03 persistence split change builder API?**
   - Recommendation: Keep builder input as `Playlist` Pydantic model; persistence is adapter concern in Phase 5.

## Environment Availability

**Step 2.6: SKIPPED** — Phase 4 is pure Python domain logic with no external runtime dependencies. Tests run via existing `uv run pytest tests/unit -q`.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest ≥8.0 + pytest-asyncio ≥0.24 |
| Config file | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `cd backend && uv run pytest tests/unit/test_playlist_builder.py tests/unit/test_multipart.py -q` |
| Full suite command | `cd backend && uv run ruff check . && uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLT-02 | Emits up to N slots | unit golden | `pytest tests/unit/test_playlist_builder.py -k episode_count -x` | ❌ Wave 0 |
| PLT-04 | Row mode respected | unit | `pytest tests/unit/test_playlist_builder.py -k row_mode -x` | ❌ Wave 0 |
| PLT-05 | Ordered serial from resume | unit | `pytest tests/unit/test_ordered_picker.py -x` | ❌ Wave 3 |
| PLT-06 | Policies remove/restart/disordered | unit | `pytest tests/unit/test_completion_policies.py -x` | ❌ Wave 2 |
| SCH-02 | Multipart contiguous ordered | unit + property | `pytest tests/unit/test_multipart.py -x` | ❌ Wave 1 |
| ROADMAP | Day-key seed stability | unit | `pytest tests/unit/test_disordered_picker.py -k seed_stable -x` | ❌ Wave 4 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/test_<module>.py -q`
- **Per wave merge:** `uv run pytest tests/unit -q`
- **Phase gate:** Full `uv run pytest` green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/fixtures/playlist_vectors.py` — episode factories with multipart helpers
- [ ] `domain/playlist.py` — config + result models
- [ ] `core/playlist/` package scaffold
- [ ] Optional: `uv add --dev hypothesis` — property tests Wave 6

## Security Domain

Phase 4 has no auth surface. Input validation via Pydantic on domain models satisfies structural integrity only.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Pydantic models on `Playlist`, `SeriesRebuildInput` |
| V6 Cryptography | no | — |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Invalid config (N=0, duplicate rows) | Tampering | Pydantic `Field(ge=1)`; builder rejects empty active pool |

## Suggested Plan Breakdown (MVP Vertical Slices)

| Wave | Plan focus | Delivers | Requirements |
|------|------------|----------|--------------|
| **0** | Domain models + test fixtures | `domain/playlist.py`, `playlist_vectors.py` | PLT-01–04 scaffolding |
| **1** | Multipart module | `multipart.py`, `test_multipart.py`, adjacency goldens | SCH-02 core |
| **2** | Completion policies | `completion.py`, `test_completion_policies.py` | PLT-06 |
| **3** | Ordered picker | `ordered.py`, `test_ordered_picker.py`, resume integration | PLT-05 |
| **4** | Disordered picker + seed | `disordered.py`, `test_disordered_picker.py`, day-key vectors | PLT-04, ROADMAP seed |
| **5** | PlaylistBuilder integration | `builder.py`, `test_playlist_builder.py` end-to-end | PLT-02, all |
| **6** (optional) | Hypothesis properties | `@given` invariants for adjacency + seed | ROADMAP property tests |

**Explicitly OUT of scope for all waves:** Alembic migrations, `/api/v1/playlists` routes, SPA screens, APScheduler, WheelOfFish, MediaProvider calls inside builder.

## Project Constraints (from .cursor/rules/)

No `.cursor/rules/` directory found in workspace — no additional project-specific enforcement beyond user rules and GSD config (`nyquist_validation: true`, `commit_docs: true`).

## Sources

### Primary (HIGH confidence)
- `backend/src/wheeloffish/core/resume.py` — resume algorithm implemented and tested
- `backend/src/wheeloffish/domain/dto.py` — Episode/ResumeCursor shapes
- `backend/src/wheeloffish/integrations/plex/mappers.py` — `multipartGroupId` / `partIndex` mapping
- `backend/src/wheeloffish/integrations/jellyfin/mappers.py` — Jellyfin multipart fields
- `backend/src/wheeloffish/api/routes/catalog.py` — episode + resume fetch contract for Phase 5
- `backend/tests/unit/test_resume_service.py` — golden-vector pattern to mirror
- `.planning/phases/02-media-ingestion-catalogs/02-CONTEXT.md` — D-10–D-13, D-21 locked semantics
- `.planning/ROADMAP.md` Phase 4 success criteria

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` PLT-01–06, SCH-02
- `.planning/PROJECT.md` product description (ordered binge + disordered feathers + multipart)
- `.planning/research/SUMMARY.md` — multipart pitfall notes, deterministic block ordering

### Tertiary (LOW confidence — validate in discuss/plan)
- Slot allocation fairness model (uniform with replacement)
- Multipart block includes all parts vs tail-only

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — stdlib + existing pytest; no new runtime deps required
- Architecture: **HIGH** — clear reuse of ResumeService; Phase 5 boundary explicit
- Pitfalls: **MEDIUM** — slot/multipart edge cases need discuss-phase lock on A1–A8

**Research date:** 2026-05-25
**Valid until:** 2026-06-25
