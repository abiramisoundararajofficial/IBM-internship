"""Job description parsing utilities.

Simple, local parsing to extract a job title and a list of required skills.
This is intentionally lightweight to keep token usage low and to run locally.
"""

from typing import Dict, List
import re


def parse_job_description(text: str) -> Dict[str, object]:
    """Parse a job description text and return a dict with `title` and `skills`.

    - `title`: first non-empty line (or 'Not found' if none)
    - `skills`: list collected from lines starting with 'Skills' or 'Requirements'
    """
    if not text or not text.strip():
        return {"title": "Not found", "skills": []}

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0] if lines else "Not found"

    skills: List[str] = []
    for line in lines:
        low = line.lower()
        if low.startswith("skills") or low.startswith("requirements") or "skills:" in low or "requirements:" in low:
            if ":" in line:
                after = line.split(":", 1)[1]
            else:
                after = line
            tokens = re.split(r"[,;|\\-]", after)
            tokens = [t.strip() for t in tokens if t.strip()]
            skills.extend(tokens)

    return {"title": title, "skills": skills}
