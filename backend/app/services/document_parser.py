"""
Simple document parser. The assignment explicitly says production-grade
OCR is NOT required, so we keep this lean:

  - PDF     -> pypdf text extraction
  - .eml    -> mail-parser (subject + body)
  - .txt    -> read as UTF-8
  - image   -> we just note it was an image; caller can pass raw bytes to
              a vision model later if wanted. For the demo we return a
              placeholder that mentions the filename.
"""
import io
from pathlib import Path

from pypdf import PdfReader
from docx import Document


def parse_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(parts).strip()

def parse_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    return "\n".join(
        p.text for p in doc.paragraphs if p.text.strip()
    )


def parse_email(data: bytes) -> str:
    """Very light .eml parsing. Subject + plain body."""
    try:
        import mailparser
        mail = mailparser.parse_from_bytes(data)
        subject = mail.subject or ""
        body = mail.body or ""
        return f"Subject: {subject}\n\n{body}".strip()
    except Exception:
        # Fallback: just decode.
        return data.decode(errors="ignore")


def parse_text(data: bytes) -> str:
    return data.decode(errors="ignore").strip()


def parse_image(filename: str) -> str:
    """
    We don't run OCR in this demo. We return a placeholder that documents
    what the file was; the LLM will still be able to reason a bit if the
    user also typed context, or we can add pytesseract later.
    """
    return (
        f"[Image attached: {filename}. OCR not performed in demo build. "
        f"Please review the attached image for defect visual evidence.]"
    )


def parse_upload(filename: str, data: bytes) -> tuple[str, str]:
    """
    Route by extension. Returns (source_type, extracted_text).
    source_type is one of: pdf / email / image / text
    """
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf", parse_pdf(data)
    if ext == ".docx":
        return "docx", parse_docx(data)
    if ext == ".eml":
        return "email", parse_email(data)
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return "image", parse_image(filename)
    return "text", parse_text(data)
