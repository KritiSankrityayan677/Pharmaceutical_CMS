"""
Complaint persistence endpoints.

/complaints/save   - user reviewed the AI-populated form and clicks "Commit to QMS Ledger"
/complaints/       - list recent complaints
/complaints/{id}   - detail view
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Complaint
from ..schemas import ComplaintForm, SaveComplaintRequest

router = APIRouter(prefix="/complaints", tags=["complaints"])


def _next_complaint_number(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(Complaint).count() + 1
    return f"CC-{year}-{count:06d}"


@router.post("/save")
def save_complaint(req: SaveComplaintRequest, db: Session = Depends(get_db)):
    number = _next_complaint_number(db)
    c = Complaint(
        complaint_number=number,
        **req.form.model_dump(),
        ai_severity_suggested=(req.risk_assessment.severity_suggested if req.risk_assessment else None),
        ai_suggested_next_action=(req.risk_assessment.suggested_next_action if req.risk_assessment else None),
        ai_initial_risk_assessment=(req.risk_assessment.initial_risk_assessment if req.risk_assessment else None),
        ai_completeness=(req.completeness.model_dump() if req.completeness else None),
        ai_root_cause=[h.model_dump() for h in req.root_cause_hypotheses],
        ai_capa=(req.capa_recommendation.model_dump() if req.capa_recommendation else None),
        ai_summary=req.summary,
        ai_duplicate_of=req.duplicate_of_complaint_number,
        source_type=req.source_type,
        raw_input=req.raw_input,
        conversation=[m.model_dump() for m in req.conversation],
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "complaint_number": c.complaint_number}


@router.get("/")
def list_complaints(db: Session = Depends(get_db), limit: int = 50):
    rows = db.query(Complaint).order_by(Complaint.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "complaint_number": r.complaint_number,
            "customer_name": r.customer_name,
            "product_name": r.product_name,
            "batch_number": r.batch_number,
            "complaint_category": r.complaint_category,
            "ai_severity_suggested": r.ai_severity_suggested,
            "initial_severity": r.initial_severity,
            "priority": r.priority,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/{complaint_id}")
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    r = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not r:
        raise HTTPException(404, "Not found")
    return {
        "id": r.id,
        "complaint_number": r.complaint_number,
        "form": {k: getattr(r, k) for k in ComplaintForm.model_fields.keys()},
        "ai": {
            "severity_suggested": r.ai_severity_suggested,
            "suggested_next_action": r.ai_suggested_next_action,
            "initial_risk_assessment": r.ai_initial_risk_assessment,
            "completeness": r.ai_completeness,
            "root_cause_hypotheses": r.ai_root_cause,
            "capa_recommendation": r.ai_capa,
            "summary": r.ai_summary,
            "duplicate_of": r.ai_duplicate_of,
        },
        "conversation": r.conversation,
        "source_type": r.source_type,
        "raw_input": r.raw_input,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
