"""
LangGraph nodes for the conversational AIVOA Copilot.

Graph shape (see graph.py for the actual wiring):

                   START
                     |
                     v
                classify_intent  (rule + LLM fallback)
                     |
       .-------------+-------------.
       |             |             |
       v             v             v
    extract       update        question
    _fields       _fields
       |             |             |
       v             v             |
   completeness  (skip risk       |
       |          rerun unless     |
       v          category         |
   duplicate     changed)          |
       |             |             |
       v             v             |
     risk           |             |
       |             |             |
       v             |             |
   rca_capa         |             |
       |             |             |
       v             v             v
              compose_response
                     |
                     v
                    END

Design notes:
- Each node reads/writes ChatState. Non-relevant fields stay unset.
- We DON'T let the "update" path re-run the full RCA/CAPA pipeline every
  time the user tweaks a single field; that would be slow and mostly the
  same output. We keep whatever the previous risk_assessment says.
- The `question` path just answers - no form change, no risk change.
"""
from typing import Dict, Any, List

from sqlalchemy import or_

from ..database import SessionLocal
from ..models import Complaint
from ..services.llm import chat_json, chat_text
from .state import ChatState


# ===========================================================================
# 0. INTENT CLASSIFIER
# ===========================================================================
# Rule of thumb first (fast, deterministic), LLM only if ambiguous.
def _form_is_empty(form: Dict[str, Any]) -> bool:
    return not any(v for v in (form or {}).values() if v)


INTENT_SYSTEM = """You classify user messages in a pharmaceutical complaint intake chat.

The user is either:
  - "extract"  : reporting a NEW complaint (long descriptive text with product/batch/defect facts)
  - "update"   : correcting or adding a single detail to a form that's already filled
                 (e.g. "the batch is BMX240602", "affected quantity is 48 capsules",
                  "customer name is ABC Formulations Ltd")
  - "question" : asking a question about the current complaint or process
                 (e.g. "what should I do next?", "is this critical?")

Respond ONLY with JSON: {"intent": "extract" | "update" | "question"}
"""


def classify_intent(state: ChatState) -> Dict[str, Any]:
    file_text = state.get("file_text") or ""
    msg = (state.get("user_message") or "").strip()
    form = state.get("current_form") or {}

    # Hard rule: any file upload = extraction.
    if file_text.strip():
        trace = state.get("trace", []) + ["classify_intent: file present -> extract"]
        return {"intent": "extract", "trace": trace}

    # If form is empty and user typed a lot of text, treat as extract.
    if _form_is_empty(form) and len(msg) > 120:
        trace = state.get("trace", []) + ["classify_intent: empty form + long msg -> extract"]
        return {"intent": "extract", "trace": trace}

    # Otherwise ask the LLM.
    result = chat_json(
        system=INTENT_SYSTEM,
        user=f"Current form filled: {not _form_is_empty(form)}\nUser message:\n{msg}",
        temperature=0.0,
        max_tokens=50,
    )
    intent = result.get("intent", "update")
    if intent not in {"extract", "update", "question"}:
        intent = "update"
    trace = state.get("trace", []) + [f"classify_intent: LLM -> {intent}"]
    return {"intent": intent, "trace": trace}


# ===========================================================================
# 1. EXTRACT PATH - full field extraction from a doc or long prompt
# ===========================================================================
EXTRACT_SYSTEM = """You are a pharmaceutical QMS assistant.
Read the raw complaint (from an uploaded document or a description typed by the user)
and extract the intake-form fields.

Return ONLY this JSON structure. Use null when the source doesn't say. NEVER invent values.

{
  "complaint_source": "Email" | "Phone" | "Portal" | "Distributor Report" | "Regulator" | "Other" | null,
  "customer_name": string | null,
  "product_name": string | null,
  "product_strength_grade": string | null,      // e.g. "500 mg", "API grade IH", "80% w/w"
  "batch_number": string | null,                // verbatim, e.g. "BMX240602" or "LOT B240815A"
  "manufacturing_date": string | null,          // keep format as-found
  "expiry_date": string | null,
  "quantity_affected": string | null,           // include unit: "48 capsules", "3 vials", "1 drum"
  "complaint_type": "Product Quality" | "Adverse Event" | "Packaging" | "Labeling" | "Efficacy" | "Other" | null,
  "complaint_date": string | null,
  "detailed_complaint_description": string | null,  // 2-4 sentence factual summary of what happened
  "complaint_category": string | null           // e.g. "Foreign Matter Contamination", "Cross Contamination", "Physical Defect", "Sub-potency", "Wrong Strength Label"
}
"""


def extract_fields(state: ChatState) -> Dict[str, Any]:
    source = state.get("file_text") or state.get("user_message", "")
    result = chat_json(
        system=EXTRACT_SYSTEM,
        user=f"Raw complaint input:\n---\n{source}\n---",
        temperature=0.1,
        max_tokens=3000,
    )
    # Merge with current_form so keys the AI returned as null don't wipe existing values.
    current = state.get("current_form") or {}
    patch = {k: v for k, v in result.items() if v not in (None, "")}
    trace = state.get("trace", []) + [f"extract_fields: extracted {len(patch)} fields"]
    return {"form_patch": patch, "trace": trace}


# ===========================================================================
# 2. UPDATE PATH - user is correcting/adding one or two fields
# ===========================================================================
UPDATE_SYSTEM = """You are updating a pharmaceutical complaint intake form.

Given:
- The CURRENT form state
- The user's chat message

Figure out which specific field(s) the user is changing or filling. Return a JSON PATCH
containing ONLY the fields to update (do not include unchanged fields).

Available fields: complaint_source, customer_name, product_name, product_strength_grade,
batch_number, manufacturing_date, expiry_date, quantity_affected, complaint_type,
complaint_date, detailed_complaint_description, complaint_category, initial_severity, priority.

Examples:
User: "the batch number is BMX240602"
=> {"batch_number": "BMX240602"}

User: "affected quantity is 48 capsules and customer is ABC Formulations Ltd"
=> {"quantity_affected": "48 capsules", "customer_name": "ABC Formulations Ltd"}

User: "actually the severity should be Major"
=> {"initial_severity": "Major"}

If the user's message doesn't specify a form field, return {}.

Respond ONLY with the JSON patch object.
"""


def apply_updates(state: ChatState) -> Dict[str, Any]:
    current = state.get("current_form") or {}
    msg = state.get("user_message", "")
    result = chat_json(
        system=UPDATE_SYSTEM,
        user=f"Current form:\n{current}\n\nUser message:\n{msg}",
        temperature=0.1,
        max_tokens=1000,
    )
    # Drop empty / null entries.
    patch = {k: v for k, v in result.items() if v not in (None, "")}
    trace = state.get("trace", []) + [f"apply_updates: patched {list(patch.keys())}"]
    return {"form_patch": patch, "trace": trace}


# ===========================================================================
# 3. COMPLETENESS CHECK (extract path only)
# ===========================================================================
COMPLETENESS_SYSTEM = """You are a QMS complaint intake reviewer.
Given the fields extracted, decide whether the record has enough for investigation.
Minimum required: product_name, batch_number, detailed_complaint_description,
and at least one of (customer_name, complaint_source).

Return JSON:
{
  "is_complete": boolean,
  "missing_fields": [string, ...],
  "follow_up_questions": [string, ...]   // 1-3 concrete questions for the reporter
}
"""


def completeness_check(state: ChatState) -> Dict[str, Any]:
    merged = {**(state.get("current_form") or {}), **(state.get("form_patch") or {})}
    result = chat_json(system=COMPLETENESS_SYSTEM, user=f"Form:\n{merged}", temperature=0.1, max_tokens=800)
    trace = state.get("trace", []) + ["completeness_check: reviewed"]
    return {"completeness": result, "trace": trace}


# ===========================================================================
# 4. DUPLICATE CHECK (extract path only)
# ===========================================================================
def duplicate_check(state: ChatState) -> Dict[str, Any]:
    merged = {**(state.get("current_form") or {}), **(state.get("form_patch") or {})}
    batch = merged.get("batch_number")
    product = merged.get("product_name")
    category = merged.get("complaint_category")

    duplicate_no = None
    if batch or (product and category):
        db = SessionLocal()
        try:
            q = db.query(Complaint)
            if batch:
                q = q.filter(Complaint.batch_number == batch)
            else:
                q = q.filter(
                    Complaint.product_name == product,
                    Complaint.complaint_category == category,
                )
            hit = q.order_by(Complaint.id.desc()).first()
            if hit:
                duplicate_no = hit.complaint_number
        finally:
            db.close()

    trace = state.get("trace", []) + [
        f"duplicate_check: {'duplicate ' + duplicate_no if duplicate_no else 'no duplicates'}"
    ]
    return {"duplicate_of_complaint_number": duplicate_no, "trace": trace}


# ===========================================================================
# 5. RISK ASSESSMENT (extract path only)
# ===========================================================================
RISK_SYSTEM = """You are a pharmaceutical QMS Risk Assessment expert.
Given a customer complaint, assess:

{
  "severity_suggested": "Critical" | "Major" | "Minor",
  "suggested_next_action": "one concise sentence naming the next QMS step, e.g.
    'Laboratory investigation & manufacturing record review'",
  "initial_risk_assessment": "2-3 sentence risk assessment paragraph mentioning
    patient safety impact, product quality impact, and investigation focus",
  "risk_level": "Critical" | "High" | "Medium" | "Low",
  "patient_safety_impact": "1-2 sentences",
  "regulatory_impact": "1-2 sentences mentioning relevant frameworks
    (FDA 21 CFR 211, EU GMP, ICH Q10) when applicable"
}

Guidance:
- Contamination, mix-ups, wrong-strength labels, adverse events with hospitalization
  => Critical severity + Critical risk_level.
- Efficacy failure, sub-potency, significant packaging defect => Major + High.
- Cosmetic defect with no safety impact => Minor + Low.
"""


def risk_assessment(state: ChatState) -> Dict[str, Any]:
    merged = {**(state.get("current_form") or {}), **(state.get("form_patch") or {})}
    result = chat_json(system=RISK_SYSTEM, user=f"Complaint:\n{merged}", temperature=0.2, max_tokens=1500)
    # Also patch the form's initial_severity to match the AI suggestion by default
    # (user can override).
    trace = state.get("trace", []) + [f"risk_assessment: {result.get('severity_suggested')}"]
    return {"risk_assessment": result, "trace": trace}


# ===========================================================================
# 6. ROOT CAUSE + CAPA (extract path only)
# ===========================================================================
RCA_CAPA_SYSTEM = """You are a pharma QMS investigation and CAPA specialist.
Propose:
  1. 2-4 root cause hypotheses using the 5M framework (Man, Machine, Material, Method, Environment).
  2. CAPA plan separating corrective actions (fix THIS instance) from preventive actions (stop recurrence).

Return JSON:
{
  "root_cause_hypotheses": [
    {"category": "Man"|"Machine"|"Material"|"Method"|"Environment",
     "hypothesis": "...", "likelihood": "High"|"Medium"|"Low"}
  ],
  "capa_recommendation": {
    "corrective_actions": [string, ...],
    "preventive_actions": [string, ...]
  }
}
"""


def root_cause_capa(state: ChatState) -> Dict[str, Any]:
    merged = {**(state.get("current_form") or {}), **(state.get("form_patch") or {})}
    risk = state.get("risk_assessment", {})
    result = chat_json(
        system=RCA_CAPA_SYSTEM,
        user=f"Complaint form:\n{merged}\n\nRisk assessment:\n{risk}",
        temperature=0.3,
        max_tokens=2000,
    )
    trace = state.get("trace", []) + [
        f"root_cause_capa: {len(result.get('root_cause_hypotheses', []))} hypotheses"
    ]
    return {
        "root_cause_hypotheses": result.get("root_cause_hypotheses", []),
        "capa_recommendation": result.get("capa_recommendation", {}),
        "trace": trace,
    }


# ===========================================================================
# 7. SUMMARY (extract path only)
# ===========================================================================
SUMMARY_SYSTEM = """Write a single tight paragraph (3-4 sentences) that a QA
manager can read in 15 seconds: what happened, product/batch, risk level,
next-step recommendation. Return JSON: {"summary": "..."}."""


def summarize(state: ChatState) -> Dict[str, Any]:
    payload = {
        "form": {**(state.get("current_form") or {}), **(state.get("form_patch") or {})},
        "risk_assessment": state.get("risk_assessment"),
        "duplicate_of_complaint_number": state.get("duplicate_of_complaint_number"),
    }
    result = chat_json(system=SUMMARY_SYSTEM, user=str(payload), temperature=0.3, max_tokens=500)
    trace = state.get("trace", []) + ["summarize: wrote executive summary"]
    return {"summary": result.get("summary", ""), "trace": trace}


# ===========================================================================
# 8. QUESTION ANSWER (question intent)
# ===========================================================================
QUESTION_SYSTEM = """You are AIVOA Copilot for pharma QMS complaint intake.
Answer the user's question in 1-3 short sentences, grounded in the current form
state. Do not invent facts the form doesn't contain. Return JSON:
{"assistant_message": "..."}"""


def answer_question(state: ChatState) -> Dict[str, Any]:
    payload = {
        "form": state.get("current_form"),
        "history": state.get("history", [])[-6:],
        "question": state.get("user_message"),
    }
    result = chat_json(system=QUESTION_SYSTEM, user=str(payload), temperature=0.3, max_tokens=400)
    trace = state.get("trace", []) + ["answer_question: replied"]
    return {"assistant_message": result.get("assistant_message", ""), "trace": trace}


# ===========================================================================
# 9. COMPOSE RESPONSE (all paths converge here except question)
# ===========================================================================
COMPOSE_SYSTEM = """You are AIVOA Copilot for pharma QMS complaint intake.
Craft the chat reply the user will see. Requirements:
- 1-3 sentences, friendly professional tone.
- If fields were updated, name them specifically like:
  "Got it. I've updated the Batch/Lot Number to 'BMX240602' and the Affected Quantity to '48 capsules' in the form."
- If this was a new document extraction, briefly say what you extracted, e.g.:
  "PDF analysis complete. I've extracted the [customer] complaint (product [product_name], batch [batch_number]).
   Form populated on the left."
- If a duplicate was detected, mention it.
Return JSON: {"assistant_message": "..."}
"""


# Human-readable labels for field names in the chat reply.
FIELD_LABELS = {
    "complaint_source": "Complaint Source",
    "customer_name": "Customer Name",
    "product_name": "Product Name",
    "product_strength_grade": "Product Strength/Grade",
    "batch_number": "Batch/Lot Number",
    "manufacturing_date": "Manufacturing Date",
    "expiry_date": "Expiry Date",
    "quantity_affected": "Affected Quantity",
    "complaint_type": "Complaint Type",
    "complaint_date": "Complaint Date",
    "detailed_complaint_description": "Detailed Complaint Description",
    "complaint_category": "Complaint Category",
    "initial_severity": "Initial Severity",
    "priority": "Priority",
}


def compose_response(state: ChatState) -> Dict[str, Any]:
    patch = state.get("form_patch") or {}
    intent = state.get("intent", "update")

    # If the update path made no changes, respond conversationally instead
    # of pretending we did something.
    if intent == "update" and not patch:
        msg = ("I didn't spot a form field to update in that message. "
               "Try something like 'the batch number is BMX240602' or upload a document.")
        trace = state.get("trace", []) + ["compose_response: no-op reply"]
        return {"assistant_message": msg, "trace": trace}

    labelled_patch = {FIELD_LABELS.get(k, k): v for k, v in patch.items()}
    payload = {
        "intent": intent,
        "fields_updated": labelled_patch,
        "risk_severity": (state.get("risk_assessment") or {}).get("severity_suggested"),
        "duplicate_of": state.get("duplicate_of_complaint_number"),
    }
    result = chat_json(system=COMPOSE_SYSTEM, user=str(payload), temperature=0.4, max_tokens=300)
    trace = state.get("trace", []) + ["compose_response: crafted reply"]
    return {"assistant_message": result.get("assistant_message", ""), "trace": trace}
