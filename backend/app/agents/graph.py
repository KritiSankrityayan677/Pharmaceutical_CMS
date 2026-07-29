"""
LangGraph assembly for the conversational Copilot.

Uses conditional edges from `classify_intent` to route to one of three
sub-flows. All flows converge at `compose_response` (except `question`
which composes its own reply inline).
"""
from langgraph.graph import StateGraph, START, END

from .nodes import (
    classify_intent,
    extract_fields,
    apply_updates,
    completeness_check,
    duplicate_check,
    risk_assessment,
    root_cause_capa,
    summarize,
    answer_question,
    compose_response,
)
from .state import ChatState


def _route_after_intent(state: ChatState) -> str:
    intent = state.get("intent", "update")
    if intent == "extract":
        return "extract_fields"
    if intent == "question":
        return "answer_question"
    return "apply_updates"


def build_graph():
    g = StateGraph(ChatState)

    g.add_node("classify_intent", classify_intent)
    g.add_node("extract_fields", extract_fields)
    g.add_node("apply_updates", apply_updates)
    g.add_node("completeness_check", completeness_check)
    g.add_node("duplicate_check", duplicate_check)
    g.add_node("assess_risk", risk_assessment)
    g.add_node("root_cause_capa", root_cause_capa)
    g.add_node("summarize", summarize)
    g.add_node("answer_question", answer_question)
    g.add_node("compose_response", compose_response)

    g.add_edge(START, "classify_intent")

    # Conditional branch based on intent.
    g.add_conditional_edges(
        "classify_intent",
        _route_after_intent,
        {
            "extract_fields": "extract_fields",
            "apply_updates": "apply_updates",
            "answer_question": "answer_question",
        },
    )

    # EXTRACT path: full pipeline.
    g.add_edge("extract_fields", "completeness_check")
    g.add_edge("completeness_check", "duplicate_check")
    g.add_edge("duplicate_check", "assess_risk")
    g.add_edge("assess_risk", "root_cause_capa")
    g.add_edge("root_cause_capa", "summarize")
    g.add_edge("summarize", "compose_response")

    # UPDATE path: just patch fields, then compose reply.
    g.add_edge("apply_updates", "compose_response")

    # QUESTION path: node writes its own assistant_message and ends.
    g.add_edge("answer_question", END)

    # Everyone else ends at compose_response.
    g.add_edge("compose_response", END)

    return g.compile()


# Singleton - compiled once at import time.
complaint_graph = build_graph()


def run_chat(
    user_message: str,
    file_text: str | None,
    current_form: dict,
    history: list,
) -> dict:
    """Entry point called from the API layer."""
    initial: ChatState = {
        "user_message": user_message,
        "file_text": file_text,
        "current_form": current_form or {},
        "history": history or [],
        "form_patch": {},
        "root_cause_hypotheses": [],
        "trace": [],
    }
    return complaint_graph.invoke(initial)
