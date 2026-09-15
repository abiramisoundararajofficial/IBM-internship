"""Resume parsing utilities.

Stage 2: lightweight, local PDF text extraction and basic info extraction.
Uses PyMuPDF (fitz) to extract text and regex to find emails and phone numbers.
The functions avoid inventing information: when a field cannot be found,
they return the string "Not found in resume." as required.
"""

from typing import Dict, List
import re


def extract_text_from_pdf(path: str) -> str:
    """Extract and return text content from a PDF file at `path`.

    Returns an empty string on failure.
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(path)
        parts: List[str] = []
        for page in doc:
            parts.append(page.get_text())
        return "\n".join(parts)
    except Exception:
        return ""


def extract_info_from_text(text: str) -> Dict[str, object]:
    """Extract basic information from resume text.

    Returns a dict with keys: `name`, `email`, `phone`, `skills`.
    - `name`: Not found in resume. (avoid inventing)
    - `email`: first matched email or "Not found in resume."
    - `phone`: first matched phone or "Not found in resume."
    - `skills`: list of extracted skill tokens (may be empty)
    """
    # Email
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    email = email_match.group(0) if email_match else "Not found in resume."

    # Phone (very permissive)
    phone_match = re.search(r"\+?\d[\d\-(). ]{7,}\d", text)
    phone = phone_match.group(0).strip() if phone_match else "Not found in resume."

    # Skills: look for lines starting with 'Skills' or 'Technical Skills' and split
    skills: List[str] = []
    for line in text.splitlines():
        low = line.strip().lower()
        if low.startswith("skills") or low.startswith("technical skills") or "skills:" in low:
            # extract after colon if present
            if ":" in line:
                after = line.split(":", 1)[1]
            else:
                after = line
            # split common separators
            tokens = re.split(r"[,;|\u2022\\-]", after)
            tokens = [t.strip() for t in tokens if t.strip()]
            skills.extend(tokens)

    return {
        "name": "Not found in resume.",
        "email": email,
        "phone": phone,
        "skills": skills,
    }


def extract_info_from_pdf(path: str) -> Dict[str, object]:
    """Convenience: extract text from PDF then basic info.

    Returns the dict from `extract_info_from_text`.
    """
    text = extract_text_from_pdf(path)
    if not text:
        return {"name": "Not found in resume.", "email": "Not found in resume.", "phone": "Not found in resume.", "skills": []}
    return extract_info_from_text(text)
