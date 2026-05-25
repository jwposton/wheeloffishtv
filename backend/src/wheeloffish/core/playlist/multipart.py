"""Multipart grouping and adjacency expansion for playlist builder (SCH-02).

Semantics:
- D-07 (ordered): forward-from-anchor expansion via ``expand_multipart_forward``
- D-08 (disordered): full-block expansion via ``expand_multipart_full_block``
- D-10: SCH-02 adjacency enforcement for ordered rows uses forward expansion
- D-21: grouping keyed solely by native ``Episode.multipart_group_id`` (no heuristics)
"""

from collections import defaultdict
from collections.abc import Iterable

from wheeloffish.domain.dto import Episode

__all__ = [
    "expand_multipart_forward",
    "expand_multipart_full_block",
    "group_by_multipart",
    "sort_multipart_block",
]


def group_by_multipart(episodes: Iterable[Episode]) -> dict[str, list[Episode]]:
    groups: dict[str, list[Episode]] = defaultdict(list)
    for ep in episodes:
        if ep.multipart_group_id is None:
            continue
        groups[ep.multipart_group_id].append(ep)
    return dict(groups)


def sort_multipart_block(parts: list[Episode]) -> list[Episode]:
    return sorted(parts, key=lambda ep: (ep.part_index is None, ep.part_index or 0, ep.id))


def expand_multipart_full_block(
    anchor: Episode,
    episodes_by_id: dict[str, Episode],
) -> list[Episode]:
    if anchor.multipart_group_id is None:
        return [anchor]

    group_id = anchor.multipart_group_id
    members = [
        ep
        for ep in episodes_by_id.values()
        if ep.multipart_group_id == group_id
    ]
    if not any(ep.id == anchor.id for ep in members):
        members.append(anchor)

    seen: set[str] = set()
    unique: list[Episode] = []
    for ep in members:
        if ep.id in seen:
            continue
        seen.add(ep.id)
        unique.append(ep)

    return sort_multipart_block(unique)


def expand_multipart_forward(
    anchor: Episode,
    episodes_by_id: dict[str, Episode],
) -> list[Episode]:
    if anchor.multipart_group_id is None:
        return [anchor]

    full_block = expand_multipart_full_block(anchor, episodes_by_id)
    if anchor.part_index is None:
        return full_block

    forward = [
        ep
        for ep in full_block
        if ep.part_index is not None and ep.part_index >= anchor.part_index
    ]
    if not forward:
        return [anchor]
    return forward
