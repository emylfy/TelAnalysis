"""Reply-graph builder. Returns edges/nodes — no rendering."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass
class GraphData:
    nodes: list[tuple[str, str, int]]  # (id, label, weight)
    edges: list[tuple[str, str, str]]  # (source, target, label)


def build(messages: list[dict]) -> GraphData:
    """Build a directed reply graph.

    - Nodes: each `from_id` that posted, weight = message count.
    - Edges: from_id → reply_target for each reply. Self-edge for non-replies.
    """
    if not messages:
        return GraphData(nodes=[], edges=[])

    # id index for O(1) reply lookup
    id_index: dict = {}
    for m in messages:
        if not isinstance(m, dict):
            continue
        mid = m.get("id")
        if mid is not None:
            id_index[mid] = m

    name_counts: Counter[tuple[str, str]] = Counter()
    edges: list[tuple[str, str, str]] = []

    for m in messages:
        if not isinstance(m, dict):
            continue
        from_name = m.get("from")
        from_id = m.get("from_id")
        if not from_name or from_id is None or from_id in ("source", "target"):
            continue
        name_counts[(from_name, from_id)] += 1

        reply_id = m.get("reply_to_message_id")
        if reply_id is not None:
            target = id_index.get(reply_id)
            if target is not None:
                t_name = target.get("from")
                t_id = target.get("from_id")
                if t_id is not None:
                    name_counts[(t_name or "", t_id)] += 1
                    edges.append((str(from_id), str(t_id), f"{from_name}->{t_name}"))
        else:
            edges.append((str(from_id), str(from_id), str(from_name)))

    nodes = [(str(uid), name, count) for (name, uid), count in name_counts.items()]
    return GraphData(nodes=nodes, edges=edges)


def interaction_summary(messages: list[dict]) -> list[dict]:
    """Per-user interaction stats: messages sent, replies they sent,
    replies others sent to them. Useful for small chats where the
    force-directed graph is uninformative."""
    if not messages:
        return []

    # 1st pass: id → from_id index (replies may reference future-listed messages)
    id_to_user: dict = {}
    for m in messages:
        if not isinstance(m, dict):
            continue
        mid = m.get("id")
        uid = m.get("from_id")
        if mid is not None and uid:
            id_to_user[mid] = uid

    name_index: dict = {}
    sent: Counter = Counter()
    replies_sent: Counter = Counter()
    replies_received: Counter = Counter()

    for m in messages:
        if not isinstance(m, dict):
            continue
        from_id = m.get("from_id")
        if not from_id:
            continue
        name_index.setdefault(from_id, m.get("from") or from_id)
        sent[from_id] += 1
        rid = m.get("reply_to_message_id")
        if rid is not None:
            replies_sent[from_id] += 1
            target = id_to_user.get(rid)
            if target:
                replies_received[target] += 1

    rows = [
        {
            "user_id": uid,
            "user": name_index[uid],
            "sent": sent[uid],
            "replies_sent": replies_sent[uid],
            "replies_received": replies_received[uid],
        }
        for uid in sent
    ]
    rows.sort(key=lambda r: -r["sent"])
    return rows


def detect_communities(graph: GraphData) -> dict[str, int]:
    """Assign each node a community index via Louvain/greedy modularity.

    The reply graph is treated as undirected and parallel edges are collapsed
    into a single weighted edge per pair (self-loops dropped). Returns a
    ``{node_id: community_index}`` mapping the SPA uses to colour nodes.
    Best-effort: returns ``{}`` for empty/oversized graphs or if community
    detection is unavailable.
    """
    GRAPH_MAX_NODES = 800
    if not graph.nodes or len(graph.nodes) > GRAPH_MAX_NODES:
        return {}

    try:
        import networkx as nx
        from networkx.algorithms.community import greedy_modularity_communities
    except Exception:
        return {}

    node_ids = {nid for nid, _, _ in graph.nodes}

    # Aggregate parallel edges into a single weighted edge per (s,t) pair.
    edge_w: dict[tuple[str, str], int] = {}
    for s, t, _ in graph.edges:
        if s == t:
            continue  # self-loop drowns out interesting structure
        key = tuple(sorted((s, t)))
        edge_w[key] = edge_w.get(key, 0) + 1

    G = nx.Graph()
    for nid in node_ids:
        G.add_node(nid)
    for (s, t), w in edge_w.items():
        if s in node_ids and t in node_ids:
            G.add_edge(s, t, weight=w)

    communities: dict[str, int] = {}
    try:
        for idx, comm in enumerate(greedy_modularity_communities(G)):
            for n in comm:
                communities[str(n)] = idx
    except Exception:
        return {}
    return communities
