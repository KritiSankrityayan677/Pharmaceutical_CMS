"""
LangGraph shared state for the conversational copilot.

The graph handles THREE intents:
  - extract   : user uploaded a doc / pasted a full complaint  -> full extraction pipeline
  - update    : user is correcting / adding info to fields     -> field patch only
  - question  : user is asking a question about the complaint  -> chat back, no form change

Every node updates a slice of this state. The `compose_response` node
at the end always runs and produces the natural-language `assistant_message`
that renders in the chat bubble.
"""
from typing import TypedDict, Optional, List, Dict, Any


class ChatState(TypedDict, total=False):
    # ---- Inputs ----
    user_message: str                     # text the user typed in chat
    file_text: Optional[str]              # extracted text if a file was attached
    current_form: Dict[str, Any]          # form state as seen on the frontend
    history: List[Dict[str, str]]         # prior turns [{role, content}, ...]

    # ---- Routing ----
    intent: str                           # "extract" | "update" | "question"

    # ---- Node outputs ----
    form_patch: Dict[str, Any]            # ONLY the fields that changed
    risk_assessment: Optional[Dict[str, Any]]
    completeness: Optional[Dict[str, Any]]
    root_cause_hypotheses: List[Dict[str, Any]]
    capa_recommendation: Optional[Dict[str, Any]]
    summary: Optional[str]
    duplicate_of_complaint_number: Optional[str]

    # ---- Final chat message ----
    assistant_message: str

    # ---- Debug ----
    trace: List[str]
