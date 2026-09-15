"""Matching and ranking utilities.

Implements a lightweight, local candidate scoring based on skill overlap.
This keeps things simple and avoids external LLM calls to save credits.
"""

from typing import List, Dict, Tuple


def score_skills(resume_skills: List[str], job_skills: List[str]) -> Tuple[float, List[str]]:
    """Score a candidate by overlap between resume_skills and job_skills.

    Returns (score, matched_skills) where score is fraction of job_skills covered.
    """
    rs = set([s.strip().lower() for s in (resume_skills or []) if s.strip()])
    js = set([s.strip().lower() for s in (job_skills or []) if s.strip()])
    if not js:
        return 0.0, []
    matched = sorted(list(rs & js))
    score = len(matched) / len(js)
    return score, matched


def rank_candidates(job_text: str, resume_paths: List[str]) -> List[Dict[str, object]]:
    """Rank resumes (file paths) against a job description text.

    Each result is a dict with keys: `name`, `path`, `score`, `matched_skills`, `resume_skills_count`.
    This function uses the thin `src.tools` wrappers so it remains testable.
    """
    from .tools import parse_job, parse_resume

    job = parse_job(job_text)
    job_skills = job.get("skills", [])

    results: List[Dict[str, object]] = []
    for p in resume_paths:
        try:
            info = parse_resume(p)
            resume_skills = info.get("skills", [])
        except Exception:
            resume_skills = []

        score, matched = score_skills(resume_skills, job_skills)
        results.append(
            {
                "name": p.split("/")[-1].split("\\")[-1],
                "path": p,
                "score": round(score, 4),
                "matched_skills": matched,
                "resume_skills_count": len(resume_skills),
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
