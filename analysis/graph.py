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


def render_pyvis_html(graph: GraphData, height: str = "700px") -> str | None:
    """Render the reply graph as an interactive vis.js HTML.

    Drag, zoom, hover tooltips. Edge thickness ~ frequency.
    Node size ~ message count. Communities coloured via Louvain modularity
    (falls back to a single colour if networkx-community is unavailable).
    Returns the HTML string or None for empty/oversized graphs.
    """
    if not graph.nodes:
        return None

    GRAPH_PYVIS_MAX_NODES = 800
    if len(graph.nodes) > GRAPH_PYVIS_MAX_NODES:
        return None

    import networkx as nx
    from pyvis.network import Network

    G = nx.Graph()  # undirected for community detection; pyvis edges set arrow

    id_to_label = {nid: label for nid, label, _ in graph.nodes}
    weights = {nid: w for nid, _, w in graph.nodes}

    for nid, label, w in graph.nodes:
        G.add_node(nid, label=label or nid, weight=int(w))

    # Aggregate parallel edges into a single weighted edge per (s,t) pair.
    edge_w: dict[tuple[str, str], int] = {}
    for s, t, _ in graph.edges:
        if s == t:
            continue  # self-loop drowns out interesting structure
        key = tuple(sorted((s, t)))
        edge_w[key] = edge_w.get(key, 0) + 1
    for (s, t), w in edge_w.items():
        if s in id_to_label and t in id_to_label:
            G.add_edge(s, t, weight=w)

    # Community detection (best-effort; missing in older networkx)
    communities: dict[str, int] = {}
    try:
        from networkx.algorithms.community import greedy_modularity_communities

        for idx, comm in enumerate(greedy_modularity_communities(G)):
            for n in comm:
                communities[n] = idx
    except Exception:
        pass

    # Reuse the shared colorway so community colours match the rest of the
    # dashboard, then extend with extra distinct hues for graphs with many
    # communities.
    from analysis import theme as theme_mod

    palette = list(theme_mod.COLORWAY) + [
        "#6DC8EC",
        "#945FB9",
        "#FF9845",
        "#1E9493",
        "#FF99C3",
        "#9D9D9D",
    ]

    net = Network(
        height=height,
        width="100%",
        bgcolor=theme_mod.PALETTE["bg"],
        font_color=theme_mod.PALETTE["neutral_bright"],
        directed=False,
        notebook=False,
        cdn_resources="remote",
    )
    net.barnes_hut(
        gravity=-8000, central_gravity=0.3, spring_length=120, spring_strength=0.04
    )

    max_w = max((w for w in weights.values()), default=1)
    for nid in G.nodes:
        w = weights.get(nid, 1)
        size = 10 + 35 * (w / max_w) ** 0.5
        comm = communities.get(nid, 0)
        color = palette[comm % len(palette)]
        label = id_to_label.get(nid, nid)
        net.add_node(
            nid,
            label=label,
            value=w,
            title=f"<b>{label}</b><br>messages: {w:,}",
            color=color,
            size=size,
        )

    max_edge_w = max(edge_w.values(), default=1)
    for (s, t), w in edge_w.items():
        if s not in G.nodes or t not in G.nodes:
            continue
        thickness = 1 + 6 * (w / max_edge_w)
        net.add_edge(s, t, value=w, width=thickness, title=f"{w} interactions")

    # toggle physics, smooth edges
    net.set_options(
        """
        {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 200, "fit": true}
          },
          "edges": {
            "smooth": {"type": "continuous"},
            "color": {"opacity": 0.5},
            "scaling": {"min": 1, "max": 8}
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true
          }
        }
        """
    )

    return net.generate_html(notebook=False)
