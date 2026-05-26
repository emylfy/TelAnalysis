"""Reply-chain depth — how deep do quote-reply threads go.

A chain is a path in the reply DAG: msg → reply → reply-of-reply → ...
The longer the chain, the more "back-and-forth" the conversation. Flat
chats have chains of length 1 (just isolated quote-replies); deep chats
have multi-hop trees.

Pure functions; no UI."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class ChainStats:
    max_depth: int = 0  # longest chain length (in hops)
    avg_depth: float = 0.0  # average chain depth
    chain_count: int = 0  # how many chains we found
    depth_distribution: list[tuple[int, int]] = field(default_factory=list)


def analyze(messages: list[dict]) -> ChainStats:
    """Walk reply_to_message_id pointers, compute chain depth per leaf.

    A "leaf" is a message that nobody replied to. Its chain depth = the
    number of hops back to the root via reply_to_message_id chains."""
    # parent[id] = id of the message it replies to (or None)
    parent: dict[int, int] = {}
    has_reply: set[int] = set()
    msg_ids: set[int] = set()

    for m in messages:
        if not isinstance(m, dict):
            continue
        mid = m.get("id")
        if mid is None:
            continue
        msg_ids.add(mid)
        rid = m.get("reply_to_message_id")
        if rid is not None:
            parent[mid] = rid
            has_reply.add(rid)

    if not parent:
        return ChainStats()

    # Memoized depth computation: depth(leaf) = 1 + depth(parent[leaf])
    # if parent[leaf] is also a reply itself; otherwise 1.
    cache: dict[int, int] = {}

    def _depth(mid: int) -> int:
        if mid in cache:
            return cache[mid]
        rid = parent.get(mid)
        if rid is None or rid not in msg_ids:
            cache[mid] = 1
            return 1
        # Cycle guard via cache pre-set (shouldn't happen in real exports)
        cache[mid] = 0
        d = 1 + _depth(rid)
        cache[mid] = d
        return d

    # Only count chains ending at a leaf — otherwise we count every prefix
    # of every chain and inflate the distribution.
    leaves = [mid for mid in parent if mid not in has_reply]
    if not leaves:
        return ChainStats()

    depths = [_depth(mid) for mid in leaves]
    max_d = max(depths)
    avg_d = sum(depths) / len(depths)

    distribution = Counter(depths)
    distrib_pairs = sorted(distribution.items())

    return ChainStats(
        max_depth=max_d,
        avg_depth=avg_d,
        chain_count=len(leaves),
        depth_distribution=distrib_pairs,
    )
