import json
from collections import Counter

import streamlit as st
from pydantic import ValidationError

from planninggraph.schema import DecisionGraph
from planninggraph.viz import NODE_COLORS, compute_layout, render_graph


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


# ---------------------------------------------------------------------------
# Example graph (pre-filled so the app is immediately useful)
# ---------------------------------------------------------------------------

EXAMPLE_JSON = json.dumps(
    {
        "nodes": [
            {
                "id": "obj-1",
                "type": "objective",
                "label": "Fast graph retrieval",
                "description": "Retrieve planning graphs in < 200ms at p99",
            },
            {
                "id": "req-1",
                "type": "requirement",
                "label": "Persistent storage",
                "description": "Graphs must survive process restarts",
                "is_functional": True,
            },
            {
                "id": "dec-1",
                "type": "decision",
                "label": "Use PostgreSQL",
                "description": "Store graphs in Postgres with JSONB column",
                "rationale": "Team already operates Postgres; avoids new infra",
                "alternatives_considered": ["Redis", "SQLite"],
            },
            {
                "id": "risk-1",
                "type": "risk",
                "label": "Latency at scale",
                "description": "JSONB scan may be slow for large graphs",
                "severity": 0.6,
            },
        ],
        "edges": [
            {
                "id": "e-1",
                "type": "motivated_by",
                "source_id": "req-1",
                "target_id": "obj-1",
                "rationale": "Persistence directly supports the latency objective",
            },
            {
                "id": "e-2",
                "type": "implements",
                "source_id": "dec-1",
                "target_id": "req-1",
                "rationale": "Postgres satisfies the persistence requirement",
            },
            {
                "id": "e-3",
                "type": "exposes",
                "source_id": "dec-1",
                "target_id": "risk-1",
                "rationale": "JSONB at scale is an open concern",
            },
        ],
    },
    indent=2,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Decision Graph Visualizer",
    layout="wide",
)
st.title("Decision Graph Visualizer")

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

left, right = st.columns([1, 2])

with left:
    st.subheader("DecisionGraph JSON")
    raw = st.text_area(
        label="Paste or edit a DecisionGraph JSON object",
        value=EXAMPLE_JSON,
        height=500,
        label_visibility="collapsed",
    )
    render_btn = st.button("Render Graph", type="primary")

# ---------------------------------------------------------------------------
# Parse + render
# ---------------------------------------------------------------------------

dg: DecisionGraph | None = None
parse_error: str | None = None

# Auto-render on first load using the example; re-render when button clicked
if render_btn or "dg_rendered" not in st.session_state:
    try:
        data = json.loads(raw)
        dg = DecisionGraph.model_validate(data)
        st.session_state["dg_rendered"] = dg
        st.session_state["parse_error"] = None
        st.session_state["pos"] = compute_layout(dg)
        st.session_state["selected_node_id"] = None
    except json.JSONDecodeError as exc:
        st.session_state["parse_error"] = f"Invalid JSON: {exc}"
        st.session_state["dg_rendered"] = None
    except ValidationError as exc:
        st.session_state["parse_error"] = f"Schema validation failed:\n{exc}"
        st.session_state["dg_rendered"] = None

dg = st.session_state.get("dg_rendered")
parse_error = st.session_state.get("parse_error")

with right:
    st.subheader("Graph")
    if parse_error:
        st.error(parse_error)
    elif dg is not None:
        pos = st.session_state.get("pos")
        selected = st.session_state.get("selected_node_id")
        fig = render_graph(dg, selected_node_id=selected, pos=pos)

        event = st.plotly_chart(
            fig,
            use_container_width=True,
            on_select="rerun",
            selection_mode=["points"],
        )

        # Detect click → update selection
        if event and event.selection and event.selection.points:
            pt = event.selection.points[0]
            cd = pt.get("customdata")
            if cd:
                new_id = cd[0]
                if new_id != st.session_state.get("selected_node_id"):
                    st.session_state["selected_node_id"] = new_id
                    st.rerun()

        if selected:
            if st.button("Clear selection", key="clear_sel"):
                st.session_state["selected_node_id"] = None
                st.rerun()
    else:
        st.info("Enter a DecisionGraph JSON on the left and click Render Graph.")

# ---------------------------------------------------------------------------
# Sidebar — counts + selected node detail
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Graph stats")
    if dg is not None:
        st.markdown(f"**Nodes:** {len(dg.nodes)}  **Edges:** {len(dg.edges)}")

<<<<<<< fix/type-value-attributeerror
        node_counts = Counter((n.type.value if hasattr(n.type, 'value') else n.type) for n in dg.nodes)
=======
        node_counts = Counter(_enum_value(n.type) for n in dg.nodes)
>>>>>>> main
        if node_counts:
            st.subheader("Nodes by type")
            for ntype, count in sorted(node_counts.items()):
                st.write(f"- {ntype}: {count}")

<<<<<<< fix/type-value-attributeerror
        edge_counts = Counter((e.type.value if hasattr(e.type, 'value') else e.type) for e in dg.edges)
=======
        edge_counts = Counter(_enum_value(e.type) for e in dg.edges)
>>>>>>> main
        if edge_counts:
            st.subheader("Edges by type")
            for etype, count in sorted(edge_counts.items()):
                st.write(f"- {etype}: {count}")

        # Selected node detail panel
        selected_id = st.session_state.get("selected_node_id")
        if selected_id:
            node = next((n for n in dg.nodes if n.id == selected_id), None)
            if node:
                st.divider()
                st.subheader("Selected Node")
                color = NODE_COLORS[node.type]
<<<<<<< fix/type-value-attributeerror
                st.markdown(f"**{(node.type.value if hasattr(node.type, 'value') else node.type).upper()}**")
=======
                st.markdown(f"**{_enum_value(node.type).upper()}**")
>>>>>>> main
                st.markdown(f"**{node.label}**")
                if node.description:
                    st.markdown(node.description)
                if hasattr(node, "rationale") and node.rationale:
                    st.markdown(f"_Rationale:_ {node.rationale}")
                if hasattr(node, "severity"):
                    st.metric("Severity", f"{node.severity:.0%}")
                if hasattr(node, "confidence"):
                    st.metric("Confidence", f"{node.confidence:.0%}")
                if hasattr(node, "alternatives_considered") and node.alternatives_considered:
                    st.markdown("**Alternatives:** " + ", ".join(node.alternatives_considered))
                if hasattr(node, "test_type"):
                    st.markdown(f"**Test type:** {node.test_type}")
                if hasattr(node, "status"):
                    st.markdown(f"**Status:** {node.status}")
                if hasattr(node, "has_tests"):
                    st.markdown(f"**Has passing tests:** {'✓' if node.has_tests else '✗'}")

                connected = [e for e in dg.edges if selected_id in (e.source_id, e.target_id)]
                if connected:
                    st.markdown(f"**{len(connected)} edge(s):**")
                    node_map = {n.id: n for n in dg.nodes}
                    for e in connected:
                        direction = "→" if e.source_id == selected_id else "←"
                        other_id = e.target_id if e.source_id == selected_id else e.source_id
                        other = node_map.get(other_id)
                        other_label = other.label if other else other_id
<<<<<<< fix/type-value-attributeerror
                        st.write(f"- {(e.type.value if hasattr(e.type, 'value') else e.type)} {direction} **{other_label}**")
=======
                        st.write(f"- {_enum_value(e.type)} {direction} **{other_label}**")
>>>>>>> main
    else:
        st.info("No valid graph loaded.")
