"""Disordered (random-feather) picker for playlist builder (PLT-04).

Semantics:
- D-03: eligible pool excludes 15 most-recently-watched episodes
- D-04: caller-managed emitted_ids prevents same-rebuild duplication
- D-05: empty eligible pool falls back to full episode list
- D-08: multipart anchor emits full block via expand_multipart_full_block
- D-09: full block may include parts excluded by last-15 rule
- D-18: fresh stochastic output per rebuild (caller-owned seed)
- D-24: caller supplies fully-seeded random.Random — never instantiated here
"""

import random

from wheeloffish.core.playlist.multipart import expand_multipart_full_block
from wheeloffish.domain.dto import Episode

LAST_VIEWED_EXCLUSION_SIZE: int = 15

__all__ = ["LAST_VIEWED_EXCLUSION_SIZE", "compute_eligible_pool", "pick_disordered_block"]


def _ts(ep: Episode) -> float:
    assert ep.last_viewed_at is not None
    return ep.last_viewed_at.timestamp()


def compute_eligible_pool(episodes: list[Episode]) -> list[Episode]:
    watched = [ep for ep in episodes if ep.last_viewed_at is not None]
    unwatched = [ep for ep in episodes if ep.last_viewed_at is None]

    watched.sort(key=lambda ep: (-_ts(ep), ep.id))

    kept = watched[LAST_VIEWED_EXCLUSION_SIZE:] + unwatched

    if not kept:
        return sorted(episodes, key=lambda ep: ep.id)

    return sorted(kept, key=lambda ep: ep.id)


def pick_disordered_block(
    eligible_pool: list[Episode],
    episodes_by_id: dict[str, Episode],
    emitted_ids: set[str],
    rng: random.Random,
) -> list[Episode] | None:
    candidates = sorted(
        [ep for ep in eligible_pool if ep.id not in emitted_ids],
        key=lambda ep: ep.id,
    )

    if not candidates:
        fallback = sorted(
            [ep for ep in episodes_by_id.values() if ep.id not in emitted_ids],
            key=lambda ep: ep.id,
        )
        if not fallback:
            return None
        candidates = fallback

    anchor = rng.choice(candidates)
    return expand_multipart_full_block(anchor, episodes_by_id)
