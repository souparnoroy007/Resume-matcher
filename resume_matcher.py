import re
from collections import Counter

import streamlit as st


#WORD LISTS
SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "php", "kotlin", "swift",
    "sql", "mysql", "postgresql", "mongodb", "sqlite",
    "html", "css", "react", "angular", "node.js", "django", "flask", "fastapi", "streamlit",
    "pandas", "numpy", "matplotlib", "scikit-learn", "tensorflow", "pytorch",
    "machine learning", "deep learning", "data analysis", "data visualization",
    "data science", "nlp", "statistics", "excel", "power bi", "tableau",
    "git", "github", "docker", "kubernetes", "aws", "azure", "linux", "ci/cd",
    "rest api", "json", "web scraping", "automation", "selenium", "beautifulsoup",
    "web development", "software development", "cloud computing", "cybersecurity",
    "agile", "scrum", "jira", "testing", "unit testing", "debugging",
    "oop", "data structures", "algorithms",
    "problem solving", "communication", "teamwork", "leadership",
    "time management", "project management",
]


STOPWORDS = set(
    """
    a about above after all also an and any are as at be been being but by can could do does
    for from had has have having he her his how i if in into is it its may more most must no
    not of on one only or our out over own per should so some such than that the their them
    then there these they this those through to too under up us use used using very was we
    were what when where which while who will with within without would you your
    ability able across additional applicants application apply based best bring build
    candidate candidates company concepts day description detail details developing duties
    effective environment equal etc excellent experience familiar following good great help
    including join knowledge looking maintain make multiple need needs new opportunity part
    people plus position preferred prior provide qualifications related requirements required
    responsibilities responsible role skills solid strong support take team teams time
    understand understanding well work working year years ensure nice write writes share shares learn collaborate
    """.split()
)

SAMPLE_JD = """Python Developer Intern

We are looking for a Python developer intern to build data tools for our analytics team.
You will write clean Python code, work with SQL databases, and build dashboards using
Streamlit and pandas.

Requirements: Python, SQL, pandas, Git, REST API experience. Good problem solving and
communication skills.
Nice to have: Docker, AWS, machine learning, data visualization.

You will collaborate with the analytics team, test your code, and document the tools you
build. Every developer on the team writes clean code and shares what they learn."""

SAMPLE_RESUME = """Sample Student
student@email.com | +91 98765 43210

Education
B.Tech Computer Science, 2026

Skills
Python, SQL, pandas, matplotlib, HTML, CSS, Git, GitHub, problem solving, communication

Projects
Expense Tracker: Built a web app with Python, Streamlit and SQLite to record expenses and
show charts of spending by category. Wrote clean code and used pandas for data analysis.

Attendance Tool: Python developer project that reads CSV files and calculates attendance
percentages for a college class.

Experience
Member of the college coding club. Helped organise coding workshops for students."""



# TEXT HELPERS

def normalise(word):
    """Very simple plural fix: 'projects' -> 'project'."""
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "is", "us", "ics")):
        return word[:-1]
    return word


def get_words(text):
    """Split text into useful lowercase words (no stopwords, no tiny words)."""
    words = re.findall(r"[a-z][a-z+#]{2,}", text.lower())
    result = []
    for w in words:
        n = normalise(w)
        if w not in STOPWORDS and n not in STOPWORDS:
            result.append(n)
    return result


def find_skills(text):
    """Return the set of known skills that appear in the text."""
    text = text.lower()
    found = set()
    for skill in SKILLS:
        pattern = r"(?<![a-z0-9+#])" + re.escape(skill) + r"(?![a-z0-9+#])"
        if re.search(pattern, text):
            found.add(skill)
    return found


def read_pdf(file):
    """Read the text from an uploaded PDF. Returns None if pypdf is not installed."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""



#MATCHING LOGIC

def analyse(resume, job):
    """Compare the resume with the job description and return a dictionary of results."""
 
    job_skills = find_skills(job)
    resume_skills = find_skills(resume)
    matched_skills = sorted(job_skills & resume_skills)
    missing_skills = sorted(job_skills - resume_skills)


    skill_words = {normalise(w) for s in job_skills for w in re.findall(r"[a-z]+", s)}
    counts = Counter(w for w in get_words(job) if w not in skill_words)
    job_keywords = [w for w, c in counts.most_common(20) if c >= 2]
    resume_words = set(get_words(resume))
    matched_keywords = [w for w in job_keywords if w in resume_words]
    missing_keywords = [w for w in job_keywords if w not in resume_words]

   
    total = len(job_skills) * 2 + len(job_keywords)
    earned = len(matched_skills) * 2 + len(matched_keywords)
    score = round(earned / total * 100) if total else None

    return {
        "score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
    }


def check_resume(resume):
    """A quick checklist of things every resume should have."""
    lower = resume.lower()
    return {
        "Email address": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume)),
        "Phone number": bool(re.search(r"\+?\d[\d\s-]{8,}\d", resume)),
        "Education section": "education" in lower,
        "Skills section": "skills" in lower,
        "Projects or experience": "project" in lower or "experience" in lower,
    }


def chips(words, bg, fg):
    """Turn a list of words into small coloured labels (HTML)."""
    if not words:
        return "<i>none</i>"
    style = (
        f"background:{bg};color:{fg};padding:3px 10px;border-radius:12px;"
        "margin:2px;display:inline-block;font-size:0.9rem"
    )
    return " ".join(f"<span style='{style}'>{w}</span>" for w in words)



#USER INTERFACE

st.set_page_config(page_title="Resume Matcher", page_icon="📄", layout="wide")
st.title("📄 Resume vs Job Description Matcher")
st.write(
    "Paste your resume and a job description to see how well they match "
    "and which keywords you are missing."
)


def load_sample():
    """Fill both boxes with example text (handy for a quick demo)."""
    st.session_state["resume_text"] = SAMPLE_RESUME
    st.session_state["jd_text"] = SAMPLE_JD


st.button("Load sample data", on_click=load_sample)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Your resume")
    resume_text = st.text_area("Paste your resume text", key="resume_text", height=300)
    pdf_file = st.file_uploader("...or upload your resume as a PDF", type="pdf")
with col2:
    st.subheader("Job description")
    jd_text = st.text_area("Paste the job description", key="jd_text", height=300)


resume = resume_text
if pdf_file is not None:
    pdf_text = read_pdf(pdf_file)
    if pdf_text is None:
        col1.warning("To read PDFs, install pypdf:  pip install pypdf")
    elif not pdf_text.strip():
        col1.warning("Could not read text from this PDF (it may be a scanned image). Paste the text instead.")
    else:
        resume = pdf_text
        col1.caption("✅ Using the text from your uploaded PDF")

if st.button("Analyse match", type="primary"):
    if not resume.strip() or not jd_text.strip():
        st.warning("Please provide both a resume and a job description.")
        st.stop()

    result = analyse(resume, jd_text)
    if result["score"] is None:
        st.warning("Could not find enough keywords in the job description. Try pasting the full text.")
        st.stop()

    score = result["score"]
    n_matched_skills = len(result["matched_skills"])
    n_skills = n_matched_skills + len(result["missing_skills"])
    n_matched_kw = len(result["matched_keywords"])
    n_kw = n_matched_kw + len(result["missing_keywords"])

    st.divider()
    st.subheader("Result")

    m1, m2, m3 = st.columns(3)
    m1.metric("Match score", f"{score}%")
    m2.metric("Skills matched", f"{n_matched_skills} / {n_skills}")
    m3.metric("Other keywords matched", f"{n_matched_kw} / {n_kw}")
    st.progress(score / 100)

    if score >= 75:
        st.success("Strong match. Your resume fits this job well.")
    elif score >= 50:
        st.warning("Decent match. Adding the missing keywords (if you really have them) will help.")
    else:
        st.error("Low match. This job asks for a lot that your resume does not show yet.")

    left, right = st.columns(2)
    with left:
        st.markdown("#### ✅ Found in your resume")
        st.markdown("**Skills**")
        st.markdown(chips(result["matched_skills"], "#d1fae5", "#065f46"), unsafe_allow_html=True)
        st.markdown("**Other keywords**")
        st.markdown(chips(result["matched_keywords"], "#d1fae5", "#065f46"), unsafe_allow_html=True)
    with right:
        st.markdown("#### ❌ Missing from your resume")
        st.markdown("**Skills**")
        st.markdown(chips(result["missing_skills"], "#fee2e2", "#991b1b"), unsafe_allow_html=True)
        st.markdown("**Other keywords**")
        st.markdown(chips(result["missing_keywords"], "#fee2e2", "#991b1b"), unsafe_allow_html=True)
    st.caption("Only add skills you genuinely have. Never put skills on a resume that you cannot back up.")

    st.subheader("Resume checklist")
    for item, ok in check_resume(resume).items():
        st.write(("✅ " if ok else "❌ ") + item)
