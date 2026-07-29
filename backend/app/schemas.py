"""
v2 schemas.

The chat endpoint returns a PATCH (only the fields that changed) rather
than the full form. Frontend merges the patch into its Redux state, so
user edits made mid-conversation aren't blown away.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Form
# ---------------------------------------------------------------------------
class ComplaintForm(BaseModel):
    # 1. Origin & Customer Details
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None

    # 2. Product & Batch Identification
    product_name: Optional[str] = None
    product_strength_grade: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[str] = None

    # 3. Complaint Details
    complaint_type: Optional[str] = None
    complaint_date: Optional[str] = None
    detailed_complaint_description: Optional[str] = None

    # 4. Defect Analysis (AI risk assessment goes into its own object below;
    #    this section holds the complaint category the user/AI picks)
    complaint_category: Optional[str] = None

    # 5. Initial Assessment & Priority
    initial_severity: Optional[str] = None
    priority: Optional[str] = None


# ---------------------------------------------------------------------------
# AI Copilot Risk Assessment (embedded inside Section 4 on the form)
# ---------------------------------------------------------------------------
class RiskAssessment(BaseModel):
    severity_suggested: str          # Critical / Major / Minor
    suggested_next_action: str
    initial_risk_assessment: str
    risk_level: Optional[str] = None # Critical / High / Medium / Low - kept for badge
    patient_safety_impact: Optional[str] = None
    regulatory_impact: Optional[str] = None


# ---------------------------------------------------------------------------
# Bonus AI outputs
# ---------------------------------------------------------------------------
class CompletenessCheck(BaseModel):
    is_complete: bool = False
    missing_fields: List[str] = []
    follow_up_questions: List[str] = []


class RootCauseHypothesis(BaseModel):
    category: str
    hypothesis: str
    likelihood: str


class CAPARecommendation(BaseModel):
    corrective_actions: List[str] = []
    preventive_actions: List[str] = []


# ---------------------------------------------------------------------------
# Chat request / response
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str        # "user" | "assistant"
    content: str


class ChatResponse(BaseModel):
    """Response from POST /ai/chat."""
    form_patch: Dict[str, Any] = {}        # only fields that changed
    risk_assessment: Optional[RiskAssessment] = None
    completeness: Optional[CompletenessCheck] = None
    root_cause_hypotheses: List[RootCauseHypothesis] = []
    capa_recommendation: Optional[CAPARecommendation] = None
    summary: Optional[str] = None
    duplicate_of_complaint_number: Optional[str] = None

    assistant_message: str                 # what the chat bubble displays
    intent: str                            # extract | update | question  (for debug)
    extraction_progress: int = 100         # 0-100, for the progress bar


# ---------------------------------------------------------------------------
# Save request
# ---------------------------------------------------------------------------
class SaveComplaintRequest(BaseModel):
    form: ComplaintForm
    risk_assessment: Optional[RiskAssessment] = None
    completeness: Optional[CompletenessCheck] = None
    root_cause_hypotheses: List[RootCauseHypothesis] = []
    capa_recommendation: Optional[CAPARecommendation] = None
    summary: Optional[str] = None
    duplicate_of_complaint_number: Optional[str] = None
    source_type: str = "prompt"
    raw_input: str = ""
    conversation: List[ChatMessage] = []
