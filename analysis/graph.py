"""Reply-graph builder. Returns edges/nodes — no rendering."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import i18n

from .utils import display_name


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
        name_index.setdefault(from_id, display_name(m.get("from"), from_id))
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
    """Assign each node a community index via Louvain community detection.

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
        from networkx.algorithms.community import louvain_communities
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
        # seed фиксирует разбиение — цвета сообществ стабильны между запусками
        for idx, comm in enumerate(louvain_communities(G, weight="weight", seed=42)):
            for n in comm:
                communities[str(n)] = idx
    except Exception:
        return {}
    return communities


def _pct(vals: list[float], q: float) -> float:
    """Nearest-rank percentile (q in 0..1); 0 for an empty list."""
    if not vals:
        return 0.0
    s = sorted(vals)
    i = max(0, min(len(s) - 1, round((len(s) - 1) * q)))
    return s[i]


def analyse_structure(
    graph: GraphData, communities: dict[str, int], summary: list[dict]
) -> dict:
    """Turn the reply structure into something actionable: a per-participant
    *role* and a chat-level *portrait*.

    Mutates each ``summary`` row in place, adding ``role`` / ``degree`` /
    ``betweenness``, and returns a ``portrait`` dict of chat-wide findings.
    Best-effort: roles still work without networkx (just no ``bridge`` role,
    betweenness 0).

    Roles (one per person, by salience):
      - ``bridge``    high betweenness + partners span 3+ clusters (the glue)
      - ``magnet``    replied-to far more than they reply (attention sink)
      - ``echo``      replies a lot, rarely gets replies back
      - ``connector`` talks with many people, fairly balanced (a hub)
      - ``periphery`` one or no reply partners
      - ``regular``   everyone else
    """
    rows_by_id = {str(r["user_id"]): r for r in summary}

    # directed pair counts (skip self-loops = non-reply messages)
    dir_pairs: dict[tuple[str, str], int] = {}
    for s, t, _ in graph.edges:
        if s == t:
            continue
        dir_pairs[(s, t)] = dir_pairs.get((s, t), 0) + 1

    out_p: dict[str, set] = {}
    in_p: dict[str, set] = {}
    for s, t in dir_pairs:
        out_p.setdefault(s, set()).add(t)
        in_p.setdefault(t, set()).add(s)

    def degree(u: str) -> int:
        return len(out_p.get(u, set()) | in_p.get(u, set()))

    def span(u: str) -> int:
        """How many distinct communities a user's partners belong to."""
        parts = out_p.get(u, set()) | in_p.get(u, set())
        return len({communities[p] for p in parts if p in communities})

    # betweenness centrality — who sits on the paths between groups. Sampled on
    # large graphs for speed; 0 everywhere if networkx is missing.
    betw: dict[str, float] = {}
    try:
        import networkx as nx

        node_ids = {nid for nid, _, _ in graph.nodes}
        edge_w: dict[tuple[str, str], int] = {}
        for (s, t), w in dir_pairs.items():
            key = tuple(sorted((s, t)))
            edge_w[key] = edge_w.get(key, 0) + w
        G = nx.Graph()
        G.add_nodes_from(node_ids)
        for (s, t), w in edge_w.items():
            if s in node_ids and t in node_ids:
                G.add_edge(s, t, weight=w)
        if G.number_of_edges():
            n = G.number_of_nodes()
            if n > 300:
                betw = nx.betweenness_centrality(G, k=min(n, 200), seed=42, normalized=True)
            else:
                betw = nx.betweenness_centrality(G, normalized=True)
    except Exception:
        betw = {}

    active = [uid for uid in rows_by_id if degree(uid) >= 1]
    deg_p80 = _pct([degree(u) for u in active], 0.80)
    recv_p75 = _pct([rows_by_id[u]["replies_received"] for u in active], 0.75)
    sent_p75 = _pct([rows_by_id[u]["replies_sent"] for u in active], 0.75)

    # bridges: top betweenness among well-connected, community-spanning people
    bridge_cands = sorted(
        (u for u in active if degree(u) >= 3 and span(u) >= 3 and betw.get(u, 0) > 0),
        key=lambda u: betw.get(u, 0.0),
        reverse=True,
    )
    bridge_set = set(bridge_cands[:4])

    for uid, r in rows_by_id.items():
        deg = degree(uid)
        recv = r["replies_received"]
        sent_r = r["replies_sent"]
        r["degree"] = deg
        r["betweenness"] = round(betw.get(uid, 0.0), 4)
        if deg == 0:
            role = "periphery"
        elif uid in bridge_set:
            role = "bridge"
        elif recv >= max(3, recv_p75) and recv >= 1.7 * max(1, sent_r):
            role = "magnet"
        elif sent_r >= max(3, sent_p75) and sent_r >= 1.7 * max(1, recv):
            role = "echo"
        elif deg >= max(3, deg_p80):
            role = "connector"
        elif deg <= 1:
            role = "periphery"
        else:
            role = "regular"
        r["role"] = role

    # ---- chat-level portrait -------------------------------------------------
    recvs = [rows_by_id[u]["replies_received"] for u in active]
    total_recv = sum(recvs)
    top3 = sum(sorted(recvs, reverse=True)[:3])
    top3_share = top3 / total_recv if total_recv else 0.0
    connected = len(active)
    if connected < 6:
        central = "small"
    elif top3_share > 0.55:
        central = "centralized"
    elif top3_share < 0.30:
        central = "distributed"
    else:
        central = "mixed"

    csize = Counter(communities.values()) if communities else Counter()
    ncomm = sum(1 for c in csize.values() if c >= 3)

    def ratio(u: str, a: str, b: str) -> float:
        return rows_by_id[u][a] / max(1, rows_by_id[u][b])

    anon_prefix = i18n.t("Аноним")

    def pick(cands: list[str], by: str) -> str | None:
        """Highest-volume exemplar, preferring a named account over an anonymous
        one (anon is shown only when there's no named candidate)."""
        if not cands:
            return None
        ordered = sorted(cands, key=lambda u: rows_by_id[u][by], reverse=True)
        named = [u for u in ordered if not rows_by_id[u]["user"].startswith(anon_prefix)]
        return (named or ordered)[0]

    # magnet / ignored are picked by absolute volume (a real attention sink draws
    # *many* replies, not just a lopsided ratio) and kept distinct from the
    # bridges so the portrait names different people.
    mags = [u for u in active if u not in bridge_set
            and rows_by_id[u]["replies_received"] >= max(5, recv_p75)
            and rows_by_id[u]["replies_received"] >= 1.7 * max(1, rows_by_id[u]["replies_sent"])]
    mu = pick(mags, "replies_received")
    magnet = {"name": rows_by_id[mu]["user"], "ratio": round(ratio(mu, "replies_received", "replies_sent"), 1)} if mu else None

    igs = [u for u in active if u not in bridge_set
           and rows_by_id[u]["replies_sent"] >= max(5, sent_p75)
           and rows_by_id[u]["replies_sent"] >= 1.7 * max(1, rows_by_id[u]["replies_received"])]
    iu = pick(igs, "replies_sent")
    ignored = {"name": rows_by_id[iu]["user"], "ratio": round(ratio(iu, "replies_sent", "replies_received"), 1)} if iu else None

    hub = None
    if active:
        u = max(active, key=degree)
        hub = {"name": rows_by_id[u]["user"], "degree": degree(u)}

    portrait = {
        "participants": len(rows_by_id),
        "connected": connected,
        "communities": ncomm,
        "centralization": central,
        "top3_share": round(top3_share, 2),
        "bridges": [rows_by_id[u]["user"] for u in bridge_cands[:3]],
        "magnet": magnet,
        "ignored": ignored,
        "hub": hub,
    }
    return portrait
