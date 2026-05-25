"""Playlist builder orchestrator (D-01, D-02, D-23, D-24).

Pure playlist mathematics — no DB, HTTP, or scheduler coupling.
Phase 5 calls ``PlaylistBuilder.build()`` with live episode snapshots.
"""

from __future__ import annotations

import hashlib
import random

from wheeloffish.domain.playlist import SlotAllocation

__all__ = ["make_build_rng", "allocate_slots"]


def make_build_rng(playlist_id: str, rebuild_seed: str) -> random.Random:
    seed = int.from_bytes(
        hashlib.sha256(f"{playlist_id}:{rebuild_seed}".encode()).digest()[:8],
        "big",
    )
    return random.Random(seed)


def allocate_slots(
    active_series_ids: list[str],
    n: int,
    mode: SlotAllocation,
    rng: random.Random,
) -> list[str]:
    if not active_series_ids or n <= 0:
        return []

    if mode == SlotAllocation.ROUND_ROBIN:
        ordered = sorted(active_series_ids)
        return [ordered[i % len(ordered)] for i in range(n)]

    if mode == SlotAllocation.BALANCED:
        counts: dict[str, int] = {sid: 0 for sid in active_series_ids}
        assignments: list[str] = []
        for _ in range(n):
            min_count = min(counts.values())
            candidates = sorted(
                sid for sid, count in counts.items() if count == min_count
            )
            pick = rng.choice(candidates)
            assignments.append(pick)
            counts[pick] += 1
        return assignments

    # WILD (default)
    return [rng.choice(active_series_ids) for _ in range(n)]
