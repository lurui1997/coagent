"""Agent 运行态知识图谱 — 从故障事件构建实体关系。"""

from __future__ import annotations

from typing import Any

REL_LABELS = {
    "triggered": "触发",
    "routed_to": "路由",
    "hypothesized": "根因",
    "recommended": "处置",
    "scored": "评分",
}

NODE_COLORS = {
    "agent": "#0284c7",
    "incident": "#2563eb",
    "playbook": "#d97706",
    "root_cause": "#dc2626",
    "action": "#059669",
    "score": "#5c5470",
}


def build_knowledge_graph(incidents: list[dict], playbooks: dict[str, dict] | None = None) -> dict[str, Any]:
    """构建 Agent / 事件 / 根因 / 处置 关联图。"""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(node_id: str, ntype: str, label: str, **props: Any) -> None:
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "type": ntype, "label": label, **props}

    for inc in incidents:
        trace_id = inc["trace_id"]
        agent_id = inc["agent_id"]
        scenario_id = inc.get("scenario_id", "")
        llm = inc.get("llm_json") or {}
        score = inc.get("score_json") or {}

        add_node(f"agent:{agent_id}", "agent", agent_id, agent_id=agent_id)
        add_node(f"incident:{trace_id}", "incident", trace_id, scenario_id=scenario_id, status=inc.get("status"))
        edges.append({"from": f"agent:{agent_id}", "to": f"incident:{trace_id}", "rel": "triggered"})

        pb_id = _playbook_id(scenario_id, playbooks)
        if pb_id:
            ops_id = (playbooks or {}).get(pb_id, {}).get("ops_id", pb_id)
            add_node(f"playbook:{pb_id}", "playbook", ops_id, playbook_id=pb_id)
            edges.append({"from": f"incident:{trace_id}", "to": f"playbook:{pb_id}", "rel": "routed_to"})

        for i, hyp in enumerate(llm.get("hypothesis") or []):
            rc_id = f"root:{trace_id}:{i}"
            add_node(rc_id, "root_cause", hyp[:48], full=hyp)
            edges.append({"from": f"incident:{trace_id}", "to": rc_id, "rel": "hypothesized"})

        for step in llm.get("steps") or []:
            act_id = f"action:{trace_id}:{step.get('order', 0)}"
            add_node(act_id, "action", step.get("action", "")[:40], risk=step.get("risk"))
            edges.append({"from": f"incident:{trace_id}", "to": act_id, "rel": "recommended"})

        if score.get("total") is not None:
            sc_id = f"score:{trace_id}"
            add_node(sc_id, "score", f"{score['total']} {score.get('grade', '')}", total=score["total"])
            edges.append({"from": f"incident:{trace_id}", "to": sc_id, "rel": "scored"})

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "agents": len([n for n in nodes.values() if n["type"] == "agent"]),
            "incidents": len([n for n in nodes.values() if n["type"] == "incident"]),
        },
        "rel_labels": REL_LABELS,
        "node_colors": NODE_COLORS,
    }


def query_multi_hop(graph: dict[str, Any], agent_id: str, max_hops: int = 2) -> dict[str, Any]:
    """多跳查询：Agent → 事件 → 根因/处置。"""
    start = f"agent:{agent_id}"
    node_map = {n["id"]: n for n in graph["nodes"]}
    adj: dict[str, list[tuple[str, str]]] = {}
    for e in graph["edges"]:
        adj.setdefault(e["from"], []).append((e["to"], e["rel"]))

    visited: set[str] = set()
    paths: list[list[dict]] = []

    def walk(node_id: str, path: list[dict], depth: int) -> None:
        if depth > max_hops or node_id in visited:
            return
        visited.add(node_id)
        if node_id in node_map:
            path = path + [{"node": node_map[node_id], "depth": depth}]
        if depth == max_hops or node_id not in adj:
            if len(path) > 1:
                paths.append(path)
            return
        for nxt, rel in adj.get(node_id, []):
            walk(nxt, path + [{"rel": rel}], depth + 1)

    if start in node_map:
        walk(start, [], 0)

    return {"agent_id": agent_id, "paths": paths[:20], "path_count": len(paths)}


def _playbook_id(scenario_id: str, playbooks: dict[str, dict] | None) -> str | None:
    mapping = {"s1": "cs_rate_limit", "s2": "rag_empty_retrieval", "s3": "cost_over_budget"}
    return mapping.get(scenario_id) or scenario_id
