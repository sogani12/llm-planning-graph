"""
Visualization utilities for DecisionGraph.

Public API:
    compute_layout(dg) -> dict
    render_graph(dg, selected_node_id=None, pos=None) -> plotly.graph_objects.Figure
"""

from __future__ import annotations

import math

import networkx as nx
import plotly.graph_objects as go

from planninggraph.schema import DecisionGraph, EdgeType, NodeType

NODE_COLORS = {
    NodeType.OBJECTIVE:   "#4C9BE8",
    NodeType.REQUIREMENT: "#56C271",
    NodeType.ASSUMPTION:  "#F0A500",
    NodeType.DECISION:    "#9B59B6",
    NodeType.COMPONENT:   "#95A5A6",
    NodeType.INTERFACE:   "#1ABC9C",
    NodeType.RISK:        "#E74C3C",
    NodeType.TEST:        "#06B6D4",
}

EDGE_COLORS = {
    EdgeType.MOTIVATED_BY:   "#555555",
    EdgeType.ASSUMES:        "#F0A500",
    EdgeType.IMPLEMENTS:     "#56C271",
    EdgeType.DEPENDS_ON:     "#555555",
    EdgeType.CONFLICTS_WITH: "#E74C3C",
    EdgeType.INVALIDATES:    "#E74C3C",
    EdgeType.EXPOSES:        "#1ABC9C",
    EdgeType.CONSUMES:       "#1ABC9C",
    EdgeType.VERIFIES:       "#22C55E",
    EdgeType.GUARDS_AGAINST: "#F97316",
    EdgeType.VALIDATES:      "#8B5CF6",
}

EDGE_DASH = {
    EdgeType.MOTIVATED_BY:   "solid",
    EdgeType.ASSUMES:        "dash",
    EdgeType.IMPLEMENTS:     "solid",
    EdgeType.DEPENDS_ON:     "dot",
    EdgeType.CONFLICTS_WITH: "dash",
    EdgeType.INVALIDATES:    "solid",
    EdgeType.EXPOSES:        "solid",
    EdgeType.CONSUMES:       "dash",
    EdgeType.VERIFIES:       "dot",
    EdgeType.GUARDS_AGAINST: "dash",
    EdgeType.VALIDATES:      "dot",
}


def _truncate(text: str, max_len: int = 25) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


def _enforce_min_dist(pos: dict, min_dist: float = 1.5, iters: int = 100) -> dict:
    """Iteratively push apart nodes closer than min_dist."""
    nodes = list(pos.keys())
    p = {n: list(v) for n, v in pos.items()}
    for _ in range(iters):
        changed = False
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                u, v = nodes[i], nodes[j]
                dx = p[v][0] - p[u][0]
                dy = p[v][1] - p[u][1]
                d = math.sqrt(dx * dx + dy * dy) or 1e-9
                if d < min_dist:
                    push = (min_dist - d) / 2
                    nx_ = dx / d * push
                    ny_ = dy / d * push
                    p[u][0] -= nx_
                    p[u][1] -= ny_
                    p[v][0] += nx_
                    p[v][1] += ny_
                    changed = True
        if not changed:
            break
    return {n: tuple(v) for n, v in p.items()}


def compute_layout(dg: DecisionGraph) -> dict:
    """Compute and return node positions (cacheable separately from rendering)."""
    G = nx.DiGraph()
    node_map = {n.id: n for n in dg.nodes}
    for node in dg.nodes:
        G.add_node(node.id)
    for edge in dg.edges:
        if edge.source_id in node_map and edge.target_id in node_map:
            G.add_edge(edge.source_id, edge.target_id)

    n = max(G.number_of_nodes(), 1)
    k = 3.0 / (n ** 0.5)
    pos = nx.spring_layout(G, k=k, iterations=200, seed=42)
    pos = _enforce_min_dist(pos, min_dist=1.5, iters=100)
    scale = max(3.0, n * 0.3)
    return {node: (x * scale, y * scale) for node, (x, y) in pos.items()}


def render_graph(
    dg: DecisionGraph,
    selected_node_id: str | None = None,
    pos: dict | None = None,
) -> go.Figure:
    """Render a DecisionGraph as an interactive Plotly Figure."""
    G = nx.DiGraph()
    node_map = {n.id: n for n in dg.nodes}

    for node in dg.nodes:
        G.add_node(node.id, data=node)
    for edge in dg.edges:
        if edge.source_id in node_map and edge.target_id in node_map:
            G.add_edge(edge.source_id, edge.target_id, data=edge)

    if pos is None:
        pos = compute_layout(dg)

    # Determine neighbors of selected node for dimming
    neighbor_ids: set[str] = set()
    if selected_node_id:
        for e in dg.edges:
            if e.source_id == selected_node_id:
                neighbor_ids.add(e.target_id)
            elif e.target_id == selected_node_id:
                neighbor_ids.add(e.source_id)
        neighbor_ids.add(selected_node_id)

    traces: list[go.BaseTraceType] = []

    # --- Layer 1: Edge lines (one trace per EdgeType for legend) ---
    for edge_type in EdgeType:
        edges_of_type = [
            (u, v, d["data"])
            for u, v, d in G.edges(data=True)
            if d["data"].type == edge_type
        ]
        if not edges_of_type:
            continue

        xs, ys = [], []
        for u, v, _ in edges_of_type:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            xs += [x0, x1, None]
            ys += [y0, y1, None]

        edge_opacity = 0.25 if selected_node_id else 1.0
        # Keep edges involving selected node at full opacity
        if selected_node_id:
            involved = any(
                u in neighbor_ids or v in neighbor_ids
                for u, v, _ in edges_of_type
            )
            if involved:
                # Build separate traces: dimmed and highlighted
                dim_xs, dim_ys = [], []
                hi_xs, hi_ys = [], []
                for u, v, _ in edges_of_type:
                    x0, y0 = pos[u]
                    x1, y1 = pos[v]
                    if u in neighbor_ids and v in neighbor_ids:
                        hi_xs += [x0, x1, None]
                        hi_ys += [y0, y1, None]
                    else:
                        dim_xs += [x0, x1, None]
                        dim_ys += [y0, y1, None]

                if dim_xs:
                    traces.append(go.Scatter(
                        x=dim_xs, y=dim_ys,
                        mode="lines",
                        name=edge_type.value,
                        legendgroup=f"edge_{edge_type.value}",
                        showlegend=False,
                        hoverinfo="skip",
                        opacity=0.25,
                        line=dict(color=EDGE_COLORS[edge_type], dash=EDGE_DASH[edge_type], width=2),
                    ))
                if hi_xs:
                    traces.append(go.Scatter(
                        x=hi_xs, y=hi_ys,
                        mode="lines",
                        name=edge_type.value,
                        legendgroup=f"edge_{edge_type.value}",
                        showlegend=True,
                        hoverinfo="skip",
                        line=dict(color=EDGE_COLORS[edge_type], dash=EDGE_DASH[edge_type], width=2),
                    ))
                continue

        traces.append(go.Scatter(
            x=xs, y=ys,
            mode="lines",
            name=edge_type.value,
            legendgroup=f"edge_{edge_type.value}",
            showlegend=True,
            hoverinfo="skip",
            opacity=0.25 if selected_node_id else 1.0,
            line=dict(color=EDGE_COLORS[edge_type], dash=EDGE_DASH[edge_type], width=2),
        ))

    # --- Layer 2: Edge hover midpoints ---
    mid_xs, mid_ys, mid_hover = [], [], []
    for u, v, d in G.edges(data=True):
        edge = d["data"]
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        mid_xs.append((x0 + x1) / 2)
        mid_ys.append((y0 + y1) / 2)
        rationale = getattr(edge, "rationale", "") or ""
        mid_hover.append(
            f"<b>{edge.type.value}</b>"
            + (f"<br>{rationale}" if rationale else "")
        )

    if mid_xs:
        traces.append(go.Scatter(
            x=mid_xs, y=mid_ys,
            mode="markers",
            showlegend=False,
            hovertext=mid_hover,
            hoverinfo="text",
            marker=dict(size=8, opacity=0),
        ))

    # --- Layer 3: Nodes (one trace per NodeType for legend) ---
    for node_type in NodeType:
        nodes_of_type = [n for n in dg.nodes if n.type == node_type]
        if not nodes_of_type:
            continue

        # Split into selected/neighbor vs background when a node is selected
        if selected_node_id:
            bg_nodes = [n for n in nodes_of_type if n.id not in neighbor_ids]
            fg_nodes = [n for n in nodes_of_type if n.id in neighbor_ids and n.id != selected_node_id]
        else:
            bg_nodes = []
            fg_nodes = []
            # all nodes at full opacity

        all_nodes = nodes_of_type if not selected_node_id else (bg_nodes + fg_nodes)

        def _node_trace(node_list, opacity, show_legend, legend_suffix=""):
            xs = [pos[n.id][0] for n in node_list]
            ys = [pos[n.id][1] for n in node_list]
            hover = [
                f"<b>{n.type.value.upper()}</b><br>{n.label}"
                + (f"<br><br>{n.description}" if n.description else "")
                for n in node_list
            ]
            customdata = [[n.id] for n in node_list]
            return go.Scatter(
                x=xs, y=ys,
                mode="markers",
                name=node_type.value + legend_suffix,
                legendgroup=f"node_{node_type.value}",
                showlegend=show_legend,
                hovertext=hover,
                hoverinfo="text",
                customdata=customdata,
                opacity=opacity,
                marker=dict(
                    size=28,
                    color=NODE_COLORS[node_type],
                    line=dict(width=2, color="white"),
                ),
            )

        if selected_node_id:
            if bg_nodes:
                traces.append(_node_trace(bg_nodes, opacity=0.25, show_legend=False))
            if fg_nodes:
                traces.append(_node_trace(fg_nodes, opacity=1.0, show_legend=True))
        else:
            traces.append(_node_trace(nodes_of_type, opacity=1.0, show_legend=True))

    # --- Layer 4: Selected node highlight trace ---
    if selected_node_id and selected_node_id in node_map:
        sel_node = node_map[selected_node_id]
        sx, sy = pos[selected_node_id]
        traces.append(go.Scatter(
            x=[sx], y=[sy],
            mode="markers+text",
            showlegend=False,
            hoverinfo="skip",
            text=[_truncate(sel_node.label)],
            textposition="top center",
            textfont=dict(size=11, color="#333"),
            customdata=[[sel_node.id]],
            marker=dict(
                size=40,
                color=NODE_COLORS[sel_node.type],
                line=dict(width=3, color="white"),
            ),
        ))

    fig = go.Figure(data=traces)

    # --- Arrowhead annotations ---
    arrow_opacity = 1.0
    for u, v, d in G.edges(data=True):
        edge = d["data"]
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        is_active = (not selected_node_id) or (u in neighbor_ids and v in neighbor_ids)
        fig.add_annotation(
            ax=x0, ay=y0,
            x=x1, y=y1,
            xref="x", yref="y",
            axref="x", ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.5,
            arrowcolor=EDGE_COLORS[edge.type],
            arrowwidth=2,
            text="",
            opacity=0.8 if is_active else 0.15,
        )

    layout_kwargs: dict = dict(
        showlegend=True,
        legend=dict(x=1.01, y=1, bgcolor="rgba(255,255,255,0.8)"),
        hovermode="closest",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#fafafa",
        dragmode="pan",
    )

    # Zoom into selected node
    if selected_node_id and selected_node_id in pos:
        sx, sy = pos[selected_node_id]
        pad = 2.5
        layout_kwargs["xaxis"] = dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[sx - pad, sx + pad],
        )
        layout_kwargs["yaxis"] = dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[sy - pad, sy + pad],
        )

    fig.update_layout(**layout_kwargs)
    return fig
