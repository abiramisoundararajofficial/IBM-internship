"""Lightweight Agent that selects tools and optionally uses Ollama.

Design goals:
- Use deterministic keyword rules where possible to avoid LLM calls.
- Fall back to Ollama for ambiguous instructions.
- Keep the interface small: `Agent.handle(message)` returns a string
  response and may call local tool wrappers in `src.tools`.
"""

from typing import Optional
import os
from .ollama import generate as ollama_generate


class Agent:
    def __init__(self, default_model: Optional[str] = None):
        self.model = default_model

    def select_tool(self, message: str) -> Optional[str]:
        m = message.lower()
        # deterministic rules
        if "rank" in m and ("candidate" in m or "candidates" in m or "resume" in m):
            return "rank_candidates"
        if "search" in m or "find" in m or "where" in m:
            return "search_resumes"
        if "analyze resume" in m or ("analyze" in m and "resume" in m):
            return "parse_resume"
        if "job" in m and ("parse" in m or "analyze" in m):
            return "parse_job"
        # otherwise unknown
        return None

    def handle(self, message: str, context: dict = None) -> str:
        """Process `message` and call an appropriate tool when possible.

        `context` may include `resumes_dir` and `jobs_dir` paths or lists.
        """
        tool = self.select_tool(message)
        # quick local handling
        if tool == "parse_resume":
            # look for a filename mentioned in message or pick first resume
            resumes = (context or {}).get("resumes", [])
            target = None
            for r in resumes:
                if r.lower() in message.lower():
                    target = r
                    break
            if not target and resumes:
                target = resumes[0]
            if not target:
                return "No resumes available to analyze."
            from .tools import parse_resume

            info = parse_resume(str((context or {}).get("resumes_dir", "")) + os.sep + target)
            return f"Parsed resume `{target}`: {info}"

        if tool == "parse_job":
            jobs = (context or {}).get("jobs", [])
            target = None
            for j in jobs:
                if j.lower() in message.lower():
                    target = j
                    break
            if not target and jobs:
                target = jobs[0]
            if not target:
                return "No saved job descriptions available."
            jp = (context or {}).get("jobs_dir", "")
            try:
                text = open(os.path.join(jp, target)).read()
            except Exception:
                text = ""
            from .tools import parse_job

            parsed = parse_job(text)
            return f"Parsed job `{target}`: {parsed}"

        if tool == "search_resumes":
            # treat the whole message as query (strip trigger word)
            query = message
            for prefix in ["search for", "search", "find"]:
                if message.lower().startswith(prefix):
                    query = message[len(prefix) :].strip()
                    break
            resume_paths = (context or {}).get("resume_paths", [])
            from .tools import search_resumes

            results = search_resumes(query, resume_paths, top_k=5)
            if not results:
                return "No matches found."
            out = []
            for r in results:
                out.append(f"{r['path'].split(os.sep)[-1]} (score={r['score']:.3f})")
            return "Search results: " + ", ".join(out)

        if tool == "rank_candidates":
            # rank all resumes against a job name (if present)
            jobs = (context or {}).get("jobs", [])
            target_job = None
            for j in jobs:
                if j.lower() in message.lower():
                    target_job = j
                    break
            if not target_job and jobs:
                target_job = jobs[0]
            if not target_job:
                return "No job selected for ranking."
            jp = (context or {}).get("jobs_dir", "")
            try:
                job_text = open(os.path.join(jp, target_job)).read()
            except Exception:
                job_text = ""
            resume_paths = (context or {}).get("resume_paths", [])
            from .tools import rank_candidates

            results = rank_candidates(job_text, resume_paths)
            if not results:
                return "No ranking results."
            out_lines = [f"{r['name']}: score={r['score']:.3f}" for r in results]
            return "Ranking:\n" + "\n".join(out_lines)

        # fallback: ask Ollama to suggest a tool or respond
        prompt = (
            "You are a lightweight assistant that selects one of these tools for the user: "
            "parse_resume, parse_job, search_resumes, rank_candidates. "
            "User message: '" + message + "'. Reply with a short suggestion and one-line action."
        )
        ans = ollama_generate(prompt, model=self.model)
        return f"Assistant (Ollama): {ans}"


def choose_tool(intent: str):
    agent = Agent()
    return agent.select_tool(intent)
