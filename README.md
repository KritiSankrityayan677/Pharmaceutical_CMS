# AIVOA - AI-Powered Customer Complaint Management (Pharma QMS) — v2

Take-home for the AI Product Engineer role. Two-panel intake system: **Log Customer Complaint** form on the left, **conversational AIVOA Copilot** on the right. The copilot reads PDFs / emails / plain text, populates the form, and lets the user correct fields via chat ("*the batch is BMX240602 and quantity is 48 capsules*") with instant field-level patches.

**Stack (matches the assignment spec):**
- Frontend: React + Redux Toolkit (Vite)
- Backend: Python + FastAPI
- AI orchestration: LangGraph (with conditional routing between extract / update / question intents)
- LLM: Groq `gemma2-9b-it`
- Database: SQLite for dev (swap to Postgres/MySQL via `.env`)
- Font: Google Inter

---

## Reference-UI parity

Matches the reference screenshots section-by-section:

| Reference element | Implementation |
|---|---|
| "Log Customer Complaint" title + "API & FDF Quality Assurance Module" subtitle | `ComplaintForm.jsx` header |
| "Pending Triage" pill top-right | `.triage-pill` |
| Sections 1–5 with numbered headers | Five `.form-section` blocks |
| "Awaiting AI extraction…" placeholders | Placeholder on every input |
| Embedded AI Copilot Risk Assessment box (blue) in Section 4 | `RiskAssessmentBox.jsx` |
| "Commit to QMS Ledger" button | `.btn-commit` |
| "AIVOA Copilot" / "Drop complaint files or paste text below." header + BETA badge | `ChatCopilot.jsx` header |
| Drag-and-drop zone + "or click to browse" | `.dropzone` |
| "Supported formats: PDF, DOCX, TXT, EML · Max file size: 10MB" | `.format-note` |
| Extraction progress bar with % | `.progress-block` |
| Chat bubbles (user purple, AI grey) + PDF attachment card in bubble | `ChatBubble` component |
| "Type a message or paste a complaint…" composer with attach + send | `.composer` |
| "POWERED BY LANGGRAPH" footer | `.disclaimer .powered` |

---

## The three conversation flows

The LangGraph pipeline routes by **intent**, decided in the first node:

**Flow A — Extract (new complaint):** triggered by any file upload OR when the form is empty and the user pastes a long description.
```
classify_intent  →  extract_fields  →  completeness_check  →  duplicate_check
                 →  risk_assessment  →  root_cause_capa  →  summarize  →  compose_response
```

**Flow B — Update (correction):** triggered by short messages like *"batch is BMX240602"* when the form already has content.
```
classify_intent  →  apply_updates  →  compose_response
```
`apply_updates` returns ONLY the field(s) that changed. Frontend merges the patch. Frozen form + preserved user edits.

**Flow C — Question:** triggered by *"what should I do next?"*, *"is this critical?"*.
```
classify_intent  →  answer_question  →  END
```
No form change; just a chat reply grounded in the current form state.

---

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # then edit .env - fill in GROQ_API_KEY
python generate_samples.py          # writes sample PDFs (incl. Metformin/BMX240602)

uvicorn app.main:app --reload --port 8000
```

Backend is at `http://localhost:8000`. OpenAPI docs at `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

---

## API surface (v2)

| Method | Path                    | Purpose                                                   |
|--------|-------------------------|-----------------------------------------------------------|
| GET    | `/`                     | Health check + which Groq model is active                 |
| POST   | `/ai/chat`              | Unified. multipart with `message`, `current_form`, `history`, optional `file`. Returns `form_patch` + `assistant_message` + AI outputs. |
| POST   | `/complaints/save`      | Persist reviewed complaint (called by "Commit to QMS Ledger") |
| GET    | `/complaints/`          | List recent complaints                                    |
| GET    | `/complaints/{id}`      | Detail view (form + AI outputs + full chat transcript)    |

### `/ai/chat` response shape
```json
{
  "form_patch": { "batch_number": "BMX240602", "quantity_affected": "48 capsules" },
  "risk_assessment": {
    "severity_suggested": "Critical",
    "suggested_next_action": "Laboratory investigation & manufacturing record review",
    "initial_risk_assessment": "Potential foreign matter contamination…",
    "risk_level": "Critical",
    "patient_safety_impact": "…",
    "regulatory_impact": "…"
  },
  "completeness": { "is_complete": true, "missing_fields": [], "follow_up_questions": [] },
  "root_cause_hypotheses": [ { "category": "Material", "hypothesis": "…", "likelihood": "High" } ],
  "capa_recommendation": { "corrective_actions": [...], "preventive_actions": [...] },
  "summary": "…",
  "duplicate_of_complaint_number": null,
  "assistant_message": "PDF analysis complete. I've extracted the ABC Formulations complaint (product Metformin API, batch BMX240602). Form populated on the left.",
  "intent": "extract",
  "extraction_progress": 100
}
```

---

## Project layout

```
backend/
  app/
    main.py                     # FastAPI app + CORS
    config.py                   # env-driven settings
    database.py                 # SQLAlchemy engine / session
    models.py                   # Complaint ORM (5-section field layout)
    schemas.py                  # Pydantic request/response
    services/
      llm.py                    # Groq client + JSON-mode helper
      document_parser.py        # PDF / EML / image extraction
    agents/
      state.py                  # ChatState TypedDict
      nodes.py                  # 10 nodes: classify_intent, extract_fields,
                                # apply_updates, completeness_check,
                                # duplicate_check, risk_assessment,
                                # root_cause_capa, summarize,
                                # answer_question, compose_response
      graph.py                  # LangGraph assembly w/ conditional routing
    routers/
      ai.py                     # /ai/chat (unified)
      complaints.py             # /complaints CRUD
  generate_samples.py           # writes realistic pharma complaint PDFs / eml
  sample_complaints/            # generated - upload these in the demo

frontend/
  src/
    main.jsx                    # React entry + Redux Provider
    App.jsx                     # 2-column layout
    store/
      index.js
      complaintSlice.js         # form + chat history + AI state + patch merge
    api/client.js               # axios wrapper around /ai/chat + /complaints
    components/
      ComplaintForm.jsx         # 5-section form
      RiskAssessmentBox.jsx     # embedded blue AI risk box in Section 4
      ChatCopilot.jsx           # right panel: dropzone + bubbles + composer
    styles.css                  # reference-matching pharma styling
  index.html                    # loads Google Inter font
```

---

## Bonus features (all built, all check off the brief)

- [x] **Complaint Completeness Checker** — `completeness_check` node
- [x] **Root Cause Recommendation** — `root_cause_capa` node with 5M framework
- [x] **Duplicate Complaint Detection** — `duplicate_check` node (deterministic DB lookup, mentions the CC-YYYY-NNNNNN of the earlier match)
- [x] **CAPA Recommendation** — `root_cause_capa` node with corrective/preventive split
- [x] **Complaint Summary** — `summarize` node
- [x] **AI Risk Classification** — `risk_assessment` node returns severity_suggested + risk_level
- [x] **Conversational corrections** — user can chat: *"actually the batch is BMX240602"* → AI patches only that field and confirms

---

## Demo video walkthrough script (5–10 min)

The rubric wants: **input → frontend code → API → backend processing → AI/LangGraph → response populating the form + AI Copilot Risk Assessment**. Here's a tight order that covers every rubric line.

1. **(30s) Intro** — "This is an AI-powered Customer Complaint module for pharma QMS. Left panel is the intake form. Right panel is a conversational AIVOA Copilot that reads documents or plain text."
2. **(1 min) Extract flow via PDF upload** — Drag-drop `Fictional_Pharma_Customer_Complaint_01.pdf` onto the dropzone. Watch the progress bar. Show the form auto-populate and the blue Risk Assessment box appear with "Critical" severity + "Laboratory investigation & manufacturing record review" as next action.
3. **(1 min) Conversational update** — Type: `affected quantity is 48 capsules`. Show the AI reply: *"Got it. I've updated the Affected Quantity to '48 capsules' in the form."* Point out that only that ONE field changed — nothing else got overwritten.
4. **(30s) Extract flow via plain text** — Reset. Paste a shorter complaint text like "*Patient found black particles in Cefotaxime injection batch CEF-24B0715, reported from Apollo Chennai on 24 July 2026*" into the composer. Send. Show the extraction populate a different set of fields with different risk level.
5. **(30s) Duplicate detection** — Save the first complaint. Then upload the same PDF again. Point out the duplicate warning in the assistant's reply and (optionally) show the `duplicate_of_complaint_number` field in `/docs`.
6. **(2 min) Code walkthrough** — Open in this order and narrate:
   - `frontend/src/components/ChatCopilot.jsx` → dispatches `sendChatThunk` on send/drop
   - `frontend/src/store/complaintSlice.js` → shows `sendChatThunk` calling `/ai/chat` with current form + history
   - `backend/app/routers/ai.py` → receives multipart, extracts file text, calls `run_chat`
   - `backend/app/agents/graph.py` → shows the conditional edge on `classify_intent`
   - `backend/app/agents/nodes.py` → walk through `classify_intent` (rule + LLM), then `apply_updates` (the field-patch magic), then `risk_assessment` (the visible highlight)
   - `backend/app/services/llm.py` → shows the Groq `gemma2-9b-it` call with JSON mode
7. **(1 min) Persistence** — "Commit to QMS Ledger", then `GET /complaints/` in `/docs` to show the saved record with the full chat transcript preserved for audit.
8. **(30s) Close** — Recap the bonus features (completeness, duplicate, RCA, CAPA, summary, risk classification), mention what you'd add next (embeddings-based duplicate detection, human-in-the-loop CAPA approval, vision model for the image path).

---

## Notes on the design choices

- **Why a router node + conditional edges?** The reference video shows the user both uploading documents AND typing follow-up corrections into the same chat. One graph, three intents, deterministic branching keeps latency low for updates (2 LLM calls instead of 6).
- **Why return a PATCH not the full form?** User edits mid-conversation shouldn't get blown away. The AI only says "here are the specific fields I'm changing"; the frontend does a shallow merge. This is what makes the *"actually the quantity is 48 capsules"* interaction feel instant and correct.
- **Why store the AI output + chat transcript in the DB?** Pharma QMS is audit-heavy. If a Critical risk classification was AI-suggested and a QA reviewer accepted it, the whole reasoning chain must be traceable.
- **Why 5M for root cause?** Standard framework in pharma investigations; interviewers will recognise it.
- **Why sqlite by default?** Zero setup for dev. A one-line change in `.env` (`DATABASE_URL=postgresql+psycopg2://...` or `mysql+pymysql://...`) moves you to Postgres or MySQL without code changes.

---

## Troubleshooting

- **`groq.APIStatusError: 401`** — bad or missing `GROQ_API_KEY` in `.env`.
- **Extraction returns empty patch** — check the file text: hit `/docs`, upload the file, and inspect the parsed input. If empty, the PDF is image-only and needs OCR (not required for this assignment).
- **CORS errors** — confirm `FRONTEND_ORIGIN=http://localhost:5173` in backend `.env`.
- **Frontend can't reach backend** — set `VITE_API_URL` in a `frontend/.env` file if the API is not on `localhost:8000`.
