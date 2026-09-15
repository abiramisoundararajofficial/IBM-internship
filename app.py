import streamlit as st
from pathlib import Path
import pandas as pd

# Import thin tool wrappers (local parsing)
from src.tools import parse_resume, parse_job
from src.matching import rank_candidates


st.set_page_config(page_title="AI HR Recruitment Assistant", layout="wide")

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
RESUMES_DIR = DATA_DIR / "resumes"
JOBS_DIR = DATA_DIR / "jobs"
RESUMES_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)


def list_files(folder: Path):
    return sorted([p.name for p in folder.iterdir() if p.is_file()])


st.title("AI HR Recruitment Assistant — Prototype")

with st.sidebar:
    st.header("Controls")
    st.markdown(
        """
        **Responsible AI Notice**

        - The system is an AI-assisted prototype. Final hiring decisions must be made by a human recruiter.
        - The app will never invent resume information. If something is not present in a resume, the system will return: "Not found in resume."
        """
    )
    st.caption("Stage 1 UI — AI features disabled until later stages")


tabs = st.tabs([
    "Resume Upload",
    "Job Description",
    "Candidate Analysis",
    "Candidate Ranking",
    "RAG Search",
    "Interview Questions",
    "AI Recruiter Chat",
])

# Resume Upload
with tabs[0]:
    st.header("Resume Upload")
    st.write("Upload multiple PDF resumes. Files are saved locally to the `data/resumes` folder.")
    uploaded = st.file_uploader("Upload PDF resumes", accept_multiple_files=True, type=["pdf"])
    if uploaded:
        for f in uploaded:
            target = RESUMES_DIR / f.name
            with open(target, "wb") as out:
                out.write(f.getbuffer())
        st.success(f"Saved {len(uploaded)} file(s) to {RESUMES_DIR}")
        # Attempt lightweight local parsing and show summary
        parsed = []
        for f in uploaded:
            try:
                info = parse_resume(str(RESUMES_DIR / f.name))
            except Exception:
                info = {"name": "Not found in resume.", "email": "Not found in resume.", "phone": "Not found in resume.", "skills": []}
            parsed.append((f.name, info))

        st.subheader("Parsed summary")
        for name, info in parsed:
            st.write(f"**{name}**")
            st.write(info)

    st.subheader("Saved resumes")
    resumes = list_files(RESUMES_DIR)
    if resumes:
        for r in resumes:
            st.write(r)
    else:
        st.info("No resumes uploaded yet.")

# Job Description
with tabs[1]:
    st.header("Job Description")
    st.write("Paste a job description or upload a job text file (.txt, .md).")
    jd_text = st.text_area("Paste job description here", height=200)
    jd_file = st.file_uploader("Or upload a job description file", type=["txt", "md"])
    if st.button("Save job description"):
        if jd_file is not None:
            target = JOBS_DIR / jd_file.name
            with open(target, "wb") as out:
                out.write(jd_file.getbuffer())
            st.success(f"Saved job description to {target}")
            # parse and show
            try:
                text = target.read_text()
                parsed = parse_job(text)
            except Exception:
                parsed = {"title": "Not found", "skills": []}
            st.subheader("Parsed job summary")
            st.write(parsed)
        elif jd_text.strip():
            idx = len(list_files(JOBS_DIR)) + 1
            target = JOBS_DIR / f"job_{idx}.txt"
            target.write_text(jd_text)
            st.success(f"Saved job description to {target}")
            try:
                parsed = parse_job(jd_text)
            except Exception:
                parsed = {"title": "Not found", "skills": []}
            st.subheader("Parsed job summary")
            st.write(parsed)
        else:
            st.warning("No job description provided.")

    st.subheader("Saved job descriptions")
    jobs = list_files(JOBS_DIR)
    if jobs:
        for j in jobs:
            st.write(j)
    else:
        st.info("No job descriptions saved yet.")

# Candidate Analysis
with tabs[2]:
    st.header("Candidate Analysis")
    st.write("View parsed resume fields and preview a simple skill-match against a saved job.")
    resumes = list_files(RESUMES_DIR)
    jobs = list_files(JOBS_DIR)

    col1, col2 = st.columns(2)
    with col1:
        selected = st.selectbox("Select a resume to analyze", options=["-- choose --"] + resumes)
    with col2:
        selected_job = st.selectbox("Select a job to compare", options=["-- choose --"] + jobs)

    def compute_skill_match(resume_skills, job_skills):
        rs = set([s.lower() for s in resume_skills]) if resume_skills else set()
        js = set([s.lower() for s in job_skills]) if job_skills else set()
        matched = sorted(list(rs & js))
        score = 0.0
        if js:
            score = len(matched) / len(js)
        return matched, score

    if st.button("Analyze Candidate"):
        if not selected or selected == "-- choose --":
            st.warning("Please select a resume first.")
        else:
            path = RESUMES_DIR / selected
            try:
                info = parse_resume(str(path))
            except Exception:
                info = {"name": "Not found in resume.", "email": "Not found in resume.", "phone": "Not found in resume.", "skills": []}

            st.subheader("Parsed Resume Info")
            st.write(info)

            if selected_job and selected_job != "-- choose --":
                job_path = JOBS_DIR / selected_job
                try:
                    job_text = job_path.read_text()
                    job_parsed = parse_job(job_text)
                except Exception:
                    job_parsed = {"title": "Not found", "skills": []}

                job_skills = job_parsed.get("skills", [])
                resume_skills = info.get("skills", [])
                matched, score = compute_skill_match(resume_skills, job_skills)

                st.subheader("Match Preview")
                st.write({
                    "job_title": job_parsed.get("title", "Not found"),
                    "job_skills_count": len(job_skills),
                    "resume_skills_count": len(resume_skills),
                    "matched_skills": matched,
                    "score": round(score, 3),
                })
                st.info("AI-assisted recommendation. Final hiring decisions must be made by a human recruiter.")
            else:
                st.info("Select a saved job to preview matching.")

# Candidate Ranking
with tabs[3]:
    st.header("Candidate Ranking")
    st.write("Compute a simple ranking of uploaded resumes against a saved job description.")
    jobs = list_files(JOBS_DIR)
    resumes = list_files(RESUMES_DIR)

    if not resumes:
        st.info("No resumes available. Upload resumes in the 'Resume Upload' tab.")
    else:
        selected_job = st.selectbox("Select a job to rank against", options=["-- choose --"] + jobs)
        if st.button("Rank Candidates"):
            if not selected_job or selected_job == "-- choose --":
                st.warning("Please select a saved job description to rank against.")
            else:
                job_path = JOBS_DIR / selected_job
                try:
                    job_text = job_path.read_text()
                except Exception:
                    st.error("Failed to read selected job description.")
                    job_text = ""

                resume_paths = [str(RESUMES_DIR / r) for r in resumes]
                results = rank_candidates(job_text, resume_paths)
                if not results:
                    st.info("No ranking results.")
                else:
                    df = pd.DataFrame(
                        [
                            {
                                "Name": r["name"],
                                "Score": r["score"],
                                "Matched Skills": ", ".join(r["matched_skills"]) if r["matched_skills"] else "",
                                "Resume Skills Count": r["resume_skills_count"],
                            }
                            for r in results
                        ]
                    )
                    st.table(df)

from src.rag import search_resumes

# RAG Search
with tabs[4]:
    st.header("RAG-based Resume Search")
    st.write("Search across uploaded resumes using retrieval (FAISS + embeddings).")
    query = st.text_input("Enter search query")
    top_k = st.slider("Top K", min_value=1, max_value=10, value=5)
    if st.button("Search"):
        if not query.strip():
            st.warning("Please enter a search query.")
        else:
            resumes = list_files(RESUMES_DIR)
            if not resumes:
                st.info("No resumes available. Upload resumes first.")
            else:
                resume_paths = [str(RESUMES_DIR / r) for r in resumes]
                with st.spinner("Building index and searching..."):
                    try:
                        results = search_resumes(query, resume_paths, k=top_k)
                    except Exception as e:
                        st.error(f"Search failed: {e}")
                        results = []

                if not results:
                    st.info("No matches found.")
                else:
                    for r in results:
                        st.subheader(r["path"].split("/")[-1].split("\\")[-1])
                        st.write(f"Score: {r['score']:.4f}")
                        if r.get("snippet"):
                            st.write(r.get("snippet")[:1000])

# Interview Questions
with tabs[5]:
    st.header("Interview Question Generator")
    st.write("Enter a job title or skills to generate interview questions (placeholder).")
    role = st.text_input("Job title / role")
    skills = st.text_input("Key skills (comma-separated)")
    if st.button("Generate Questions"):
        if role.strip() or skills.strip():
            st.info("Question generation not enabled in Stage 1.")
        else:
            st.warning("Please enter a role or skills.")

# AI Recruiter Chat
with tabs[6]:
    st.header("AI Recruiter Chat")
    st.write("Simple chat UI. The assistant is offline in Stage 1.")
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Agent-backed chat
    from src.agent import Agent

    agent = Agent()

    chat_col, input_col = st.columns([3, 1])
    with chat_col:
        for m in st.session_state.chat_messages:
            st.write(m)
    with input_col:
        user_msg = st.text_input("Message", key="chat_input")
        if st.button("Send"):
            if user_msg.strip():
                st.session_state.chat_messages.append(f"User: {user_msg}")
                # Prepare context
                resumes = list_files(RESUMES_DIR)
                jobs = list_files(JOBS_DIR)
                context = {
                    "resumes": resumes,
                    "jobs": jobs,
                    "resumes_dir": str(RESUMES_DIR),
                    "jobs_dir": str(JOBS_DIR),
                    "resume_paths": [str(RESUMES_DIR / r) for r in resumes],
                }
                assistant_reply = agent.handle(user_msg, context=context)
                st.session_state.chat_messages.append(f"Assistant: {assistant_reply}")
                st.experimental_rerun()

    st.markdown("---")
    st.caption("Stage 1: UI-only prototype. No AI calls are made.")
