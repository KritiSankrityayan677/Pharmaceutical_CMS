"""
Complaint DB model - field names aligned with the reference UI sections:

1. Origin & Customer Details
2. Product & Batch Identification
3. Complaint Details
4. Defect Analysis (+ AI risk assessment)
5. Initial Assessment & Priority
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from .database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_number = Column(String(64), unique=True, index=True)  # e.g. CC-2026-000154

    # --- 1. Origin & Customer Details ---
    complaint_source = Column(String(128))    # Email / Phone / Portal / Distributor Report / Regulator
    customer_name = Column(String(255))       # Company or individual reporting

    # --- 2. Product & Batch Identification ---
    product_name = Column(String(255))
    product_strength_grade = Column(String(128))   # e.g. 500 mg / API grade
    batch_number = Column(String(128))             # LOT number
    manufacturing_date = Column(String(64))
    expiry_date = Column(String(64))
    quantity_affected = Column(String(64))         # "48 capsules" / "3 vials" / "1 drum"

    # --- 3. Complaint Details ---
    complaint_type = Column(String(128))           # Product Quality / Adverse Event / Packaging / Labeling / Efficacy
    complaint_date = Column(String(64))            # date reported by customer
    detailed_complaint_description = Column(Text)

    # --- 4. Defect Analysis (+ AI-suggested risk assessment) ---
    complaint_category = Column(String(128))       # Foreign Matter Contamination / Cross-contamination / Physical Defect / etc.
    ai_severity_suggested = Column(String(32))     # Critical / Major / Minor
    ai_suggested_next_action = Column(Text)
    ai_initial_risk_assessment = Column(Text)

    # --- 5. Initial Assessment & Priority (final human call) ---
    initial_severity = Column(String(32))          # Critical / Major / Minor
    priority = Column(String(32))                  # P1 / P2 / P3

    # --- Bonus AI outputs (for audit / trend) ---
    ai_completeness = Column(JSON)
    ai_root_cause = Column(JSON)
    ai_capa = Column(JSON)
    ai_summary = Column(Text)
    ai_duplicate_of = Column(String(64))

    # --- Meta ---
    source_type = Column(String(32))               # prompt / pdf / eml / txt / image
    raw_input = Column(Text)
    conversation = Column(JSON)                    # full chat transcript for audit
    created_at = Column(DateTime, default=datetime.utcnow)
