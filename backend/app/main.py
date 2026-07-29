"""
FastAPI application entry point.

Run:
    uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import ai, complaints

# Auto-create tables on startup. For a real deployment you'd use Alembic;
# for a 2-day take-home this is fine.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AIVOA Customer Complaint Management",
    version="0.1.0",
    description="AI-powered pharma QMS Customer Complaint intake with LangGraph copilot.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai.router)
app.include_router(complaints.router)


@app.get("/")
def health():
    return {"status": "ok", "model": settings.groq_model}
