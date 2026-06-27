ROUTES = {
    ("run_fail", "rate_limit"): "cs_rate_limit",
    ("run_fail", "empty_retrieval"): "rag_empty_retrieval",
    ("cost_report", "over_budget"): "cost_over_budget",
}


def route_scenario(event_type: str, symptom: str) -> str | None:
    return ROUTES.get((event_type, symptom))
