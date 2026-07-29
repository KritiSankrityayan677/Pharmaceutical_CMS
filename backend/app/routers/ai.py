"""
Unified /ai/chat endpoint.

Frontend sends multipart/form-data with:
  - message      : user's chat text (required, can be empty if just uploading a file)
  - current_form : JSON-encoded string of the current form state
  - history      : JSON-encoded list of prior {role, content} turns
  - file         : optional file upload (pdf/eml/txt/image)

Returns a ChatResponse (see schemas.py) that the frontend uses to:
  - merge form_patch into the form
  - append assistant_message to chat history
  - render/update the AI Copilot Risk Assessment box
  - show progress bar during extraction
"""
import json

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from ..schemas import ChatResponse, RiskAssessment, CompletenessCheck, RootCauseHypothesis, CAPARecommendation
from ..services.document_parser import parse_upload
from ..agents.graph import run_chat

router = APIRouter(prefix="/ai", tags=["ai"])


def _safe_json(s: str, default):
    try:
        return json.loads(s) if s else default
    except Exception:
        return default


@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(""),
    current_form: str = Form("{}"),
    history: str = Form("[]"),
    file: UploadFile | None = File(None),
):
    # Parse the JSON blobs the frontend sent as strings.
    
    print("current_form:", current_form)
    form_state = _safe_json(current_form, {})
    hist = _safe_json(history, [])

    # If a file came along, extract its text.
    file_text = None
    if file is not None:
        data = await file.read()
        _, file_text = parse_upload(file.filename or "upload", data)
        if not file_text.strip():
            raise HTTPException(422, "Could not extract text from the uploaded file")

    # Empty request guard.
    if not message.strip() and not file_text:
        raise HTTPException(400, "Empty message and no file")

    # Run the LangGraph pipeline.
    state = run_chat(
        user_message=message,
        file_text=file_text,
        current_form=form_state,
        history=hist,
    )
    print("state after run_chat:", state)

    # Map state -> response schema. Only include AI outputs that were
    # produced this turn (question intent skips risk/rca, update intent
    # skips them too - we return only what changed).
    risk = state.get("risk_assessment")
    completeness = state.get("completeness")
    rca = state.get("root_cause_hypotheses") or []
    capa = state.get("capa_recommendation")

    return ChatResponse(
        form_patch=state.get("form_patch") or {},
        risk_assessment=RiskAssessment(**risk) if risk else None,
        completeness=CompletenessCheck(**completeness) if completeness else None,
        root_cause_hypotheses=[RootCauseHypothesis(**h) for h in rca],
        capa_recommendation=CAPARecommendation(**capa) if capa else None,
        summary=state.get("summary"),
        duplicate_of_complaint_number=state.get("duplicate_of_complaint_number"),
        assistant_message=state.get("assistant_message") or "OK.",
        intent=state.get("intent", "update"),
        extraction_progress=100,
    )
