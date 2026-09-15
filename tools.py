"""Tool wrappers for the agent (Stage 1/2).

This module exposes simple functions that the agent will call. Keep wrappers
thin to make later instrumentation and permissioning simple.
"""

from typing import Dict


def parse_resume(path: str) -> Dict[str, object]:
    """Parse a resume PDF at `path` and return extracted info.

    This calls into `src.resume_parser` but keeps the surface small for the agent.
    """
    from .resume_parser import extract_info_from_pdf

    return extract_info_from_pdf(path)


def parse_job(text: str) -> Dict[str, object]:
    """Parse job description text and return parsed fields."""
    from .job_parser import parse_job_description

    return parse_job_description(text)


def search_resumes(query: str, resume_paths: list, top_k: int = 5):
    """Search resumes using src.rag.search_resumes."""
    from .rag import search_resumes as _search

    return _search(query, resume_paths, k=top_k)


def rank_candidates(job_text: str, resume_paths: list):
    """Rank candidates using src.matching.rank_candidates."""
    from .matching import rank_candidates as _rank

    return _rank(job_text, resume_paths)
