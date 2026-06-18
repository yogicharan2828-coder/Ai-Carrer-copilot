"""
AI Career Copilot - Flask Backend (Rule-Based Version)
No API key required. Works completely offline.
"""

import os
import re
import json
from flask import Flask, request, jsonify, render_template, send_file
import PyPDF2
from io import BytesIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ── Role Skill Definitions ─────────────────────────────────────────────────

ROLE_SKILLS = {
    "Software Developer": [
        "python", "java", "javascript", "typescript", "c++", "git", "docker",
        "rest api", "sql", "algorithms", "data structures", "linux", "agile",
        "unit testing", "ci/cd", "microservices"
    ],
    "Python Developer": [
        "python", "flask", "django", "fastapi", "rest api", "sql", "postgresql",
        "docker", "celery", "redis", "pytest", "git", "linux", "asyncio",
        "pandas", "sqlalchemy"
    ],
    "Frontend Developer": [
        "html", "css", "javascript", "typescript", "react", "vue", "angular",
        "tailwind", "sass", "webpack", "git", "responsive design", "rest api",
        "figma", "accessibility", "redux"
    ],
    "Machine Learning Engineer": [
        "python", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "machine learning", "deep learning", "nlp", "computer vision", "mlops",
        "docker", "kubernetes", "sql", "git", "statistics", "feature engineering"
    ],
    "Data Analyst": [
        "python", "sql", "excel", "tableau", "power bi", "pandas", "numpy",
        "statistics", "data visualization", "r", "matplotlib", "seaborn",
        "google analytics", "etl", "data cleaning", "jupyter"
    ]
}

# ── Interview Questions Database ───────────────────────────────────────────

INTERVIEW_QUESTIONS = {
    "python": {
        "beginner": [
            "What are Python's key data types?",
            "Explain the difference between a list and a tuple.",
            "What is a Python dictionary and how do you use it?",
            "How do you handle exceptions in Python?",
            "What is the difference between '==' and 'is' in Python?"
        ],
        "intermediate": [
            "Explain Python decorators and give a use case.",
            "What are generators and how do they differ from regular functions?",
            "Explain list comprehensions vs map/filter.",
            "What is the GIL and how does it affect multithreading?",
            "How does Python manage memory and garbage collection?"
        ],
        "advanced": [
            "Explain metaclasses and when you would use them.",
            "How would you optimise a Python application for performance?",
            "Describe the asyncio event loop and coroutine mechanics.",
            "How do you profile and debug memory leaks in Python?",
            "Explain the descriptor protocol and __get__ / __set__."
        ]
    },
    "machine learning": {
        "beginner": [
            "What is the difference between supervised and unsupervised learning?",
            "Explain the bias-variance tradeoff.",
            "What is overfitting and how do you prevent it?",
            "What is a confusion matrix?",
            "Explain the difference between classification and regression."
        ],
        "intermediate": [
            "How does gradient descent work?",
            "Explain cross-validation and why it is important.",
            "What is regularisation and what are L1 vs L2?",
            "How do decision trees handle missing values?",
            "Explain the ROC-AUC metric."
        ],
        "advanced": [
            "How do transformers work in NLP?",
            "Explain the mathematics behind backpropagation.",
            "How would you handle class imbalance in a dataset?",
            "What is the vanishing gradient problem and how to address it?",
            "Describe feature importance methods across different model types."
        ]
    },
    "javascript": {
        "beginner": [
            "What is the difference between var, let, and const?",
            "Explain event bubbling and capturing.",
            "What is a Promise and how does it work?",
            "What is the DOM and how do you manipulate it?",
            "Explain the difference between == and ===."
        ],
        "intermediate": [
            "What is closure in JavaScript?",
            "Explain the event loop and call stack.",
            "What are async/await and how do they relate to Promises?",
            "Explain prototypal inheritance.",
            "What is the difference between call, apply, and bind?"
        ],
        "advanced": [
            "How does the JavaScript engine optimise code?",
            "Explain memory management and garbage collection in JS.",
            "What are Web Workers and when would you use them?",
            "Describe the module bundling process with Webpack.",
            "How would you implement a virtual DOM from scratch?"
        ]
    },
    "react": {
        "beginner": [
            "What is JSX and how does it work?",
            "Explain the difference between state and props.",
            "What are React hooks? Name the most common ones.",
            "What is the virtual DOM?",
            "How does conditional rendering work in React?"
        ],
        "intermediate": [
            "When should you use useEffect vs useMemo?",
            "Explain the React component lifecycle.",
            "What is Context API and when would you use it over Redux?",
            "How do you optimise a React application's performance?",
            "What are controlled vs uncontrolled components?"
        ],
        "advanced": [
            "Explain React Fiber architecture.",
            "How would you implement code splitting in React?",
            "Describe the reconciliation algorithm.",
            "When and how would you create a custom hook?",
            "How do you handle complex state with useReducer?"
        ]
    },
    "sql": {
        "beginner": [
            "What is the difference between WHERE and HAVING?",
            "Explain the types of JOINs in SQL.",
            "What are primary keys and foreign keys?",
            "How do you write a GROUP BY query?",
            "What is the difference between DELETE and TRUNCATE?"
        ],
        "intermediate": [
            "What are window functions? Give an example.",
            "Explain database normalisation (1NF, 2NF, 3NF).",
            "How do indexes work and when should you use them?",
            "What is a CTE (Common Table Expression)?",
            "Explain the difference between UNION and UNION ALL."
        ],
        "advanced": [
            "How would you optimise a slow SQL query?",
            "Explain query execution plans.",
            "What are stored procedures and when would you use them?",
            "Describe transaction isolation levels.",
            "How do you handle deadlocks in a database?"
        ]
    },
    "docker": {
        "beginner": [
            "What is Docker and how does it differ from a VM?",
            "What is a Docker image vs a container?",
            "How do you write a basic Dockerfile?",
            "What is Docker Hub?",
            "How do you stop and remove a running container?"
        ],
        "intermediate": [
            "Explain Docker volumes and bind mounts.",
            "What is Docker Compose and when would you use it?",
            "How do Docker networks work?",
            "What is a multi-stage build?",
            "How do you pass environment variables to a container?"
        ],
        "advanced": [
            "How would you secure a Docker deployment in production?",
            "Explain Docker Swarm vs Kubernetes.",
            "How do you minimise Docker image size?",
            "Describe container orchestration patterns.",
            "How do you implement health checks in Docker?"
        ]
    }
}

GENERIC_QUESTIONS = {
    "beginner": [
        "Tell me about yourself and your background.",
        "What are your strongest technical skills?",
        "Describe a project you are most proud of.",
        "How do you stay updated with new technologies?",
        "What motivates you to pursue this role?"
    ],
    "intermediate": [
        "Describe a challenging problem you solved.",
        "How do you prioritise tasks when managing multiple deadlines?",
        "Tell me about a time you worked in a team.",
        "How do you approach debugging a difficult issue?",
        "What development methodologies have you used?"
    ],
    "advanced": [
        "How would you architect a scalable web application?",
        "Describe your experience with system design.",
        "How do you ensure code quality in a team environment?",
        "Tell me about a time you mentored someone.",
        "How do you make technical decisions under uncertainty?"
    ]
}

# ── Learning Roadmaps ──────────────────────────────────────────────────────

ROADMAPS = {
    "Software Developer": [
        {"week": 1, "title": "Version Control & Git",        "tasks": ["Master Git branching", "Learn GitHub workflow", "Practice pull requests"]},
        {"week": 2, "title": "Data Structures & Algorithms", "tasks": ["Arrays, LinkedLists, Stacks", "Sorting algorithms", "Big-O notation"]},
        {"week": 3, "title": "REST API Design",              "tasks": ["HTTP methods and status codes", "Build a simple CRUD API", "API authentication basics"]},
        {"week": 4, "title": "Databases",                    "tasks": ["SQL fundamentals", "Design schemas", "ORM basics"]},
        {"week": 5, "title": "Docker & Containerisation",    "tasks": ["Docker basics", "Write a Dockerfile", "Docker Compose for local dev"]},
        {"week": 6, "title": "CI/CD Pipelines",              "tasks": ["GitHub Actions intro", "Automate testing", "Deploy to a cloud service"]},
        {"week": 7, "title": "Testing",                      "tasks": ["Unit testing basics", "Integration tests", "Test-driven development"]},
        {"week": 8, "title": "Portfolio Project",            "tasks": ["Build a full-stack project", "Deploy it live", "Document on GitHub"]}
    ],
    "Python Developer": [
        {"week": 1, "title": "Advanced Python",    "tasks": ["Decorators & generators", "Context managers", "Type hints"]},
        {"week": 2, "title": "FastAPI",            "tasks": ["Build RESTful endpoints", "Request validation with Pydantic", "Async endpoints"]},
        {"week": 3, "title": "Database Mastery",   "tasks": ["PostgreSQL deep dive", "SQLAlchemy ORM", "Database migrations"]},
        {"week": 4, "title": "Celery & Redis",     "tasks": ["Task queues with Celery", "Redis as message broker", "Background job scheduling"]},
        {"week": 5, "title": "Docker for Python",  "tasks": ["Containerise a Flask/FastAPI app", "Docker Compose with PostgreSQL", "Environment management"]},
        {"week": 6, "title": "Testing with Pytest","tasks": ["Unit and integration tests", "Mocking and fixtures", "Coverage reports"]},
        {"week": 7, "title": "Deployment",         "tasks": ["Deploy on Render/Railway", "Configure env variables", "Set up logging"]},
        {"week": 8, "title": "API Portfolio",      "tasks": ["Build a production-ready API", "Add JWT authentication", "Publish and document"]}
    ],
    "Frontend Developer": [
        {"week": 1, "title": "HTML & CSS Mastery",       "tasks": ["Semantic HTML5", "CSS Grid & Flexbox", "Responsive design patterns"]},
        {"week": 2, "title": "JavaScript Deep Dive",     "tasks": ["ES6+ features", "DOM manipulation", "Event handling"]},
        {"week": 3, "title": "React Fundamentals",       "tasks": ["Components and props", "State management with hooks", "React Router"]},
        {"week": 4, "title": "State Management",         "tasks": ["Context API", "Redux Toolkit basics", "When to use each"]},
        {"week": 5, "title": "Styling Systems",          "tasks": ["Tailwind CSS", "CSS Modules", "Styled Components"]},
        {"week": 6, "title": "Performance",              "tasks": ["Code splitting", "Lazy loading", "Web Vitals"]},
        {"week": 7, "title": "Testing & Tooling",        "tasks": ["React Testing Library", "Vite/Webpack config", "ESLint & Prettier"]},
        {"week": 8, "title": "Portfolio Projects",       "tasks": ["Build 2-3 polished UI projects", "Deploy on Vercel", "Open-source contribution"]}
    ],
    "Machine Learning Engineer": [
        {"week": 1, "title": "Python & Math Review",  "tasks": ["NumPy & Pandas", "Linear algebra refresher", "Statistics fundamentals"]},
        {"week": 2, "title": "ML Foundations",        "tasks": ["Scikit-learn pipelines", "Train/test splits", "Evaluation metrics"]},
        {"week": 3, "title": "Deep Learning",         "tasks": ["Neural network basics", "PyTorch intro", "Training your first model"]},
        {"week": 4, "title": "NLP or CV",             "tasks": ["Choose a specialisation", "Work through tutorials", "Fine-tune a pretrained model"]},
        {"week": 5, "title": "MLOps Basics",          "tasks": ["MLflow experiment tracking", "Model versioning", "FastAPI prediction endpoint"]},
        {"week": 6, "title": "Docker & Deployment",   "tasks": ["Containerise ML API", "Deploy on cloud", "Monitoring in production"]},
        {"week": 7, "title": "Kaggle Practice",       "tasks": ["Join a competition", "Feature engineering", "Ensemble methods"]},
        {"week": 8, "title": "Capstone Project",      "tasks": ["End-to-end ML project", "Write a blog post", "GitHub portfolio"]}
    ],
    "Data Analyst": [
        {"week": 1, "title": "SQL Deep Dive",          "tasks": ["Advanced JOINs", "Window functions", "Query optimisation"]},
        {"week": 2, "title": "Python for Data",        "tasks": ["Pandas manipulation", "Data cleaning", "Missing values"]},
        {"week": 3, "title": "Data Visualisation",     "tasks": ["Matplotlib & Seaborn", "Plotly charts", "Dashboard thinking"]},
        {"week": 4, "title": "BI Tools",               "tasks": ["Tableau or Power BI", "Build a report", "Connect to live data"]},
        {"week": 5, "title": "Statistics",             "tasks": ["A/B testing", "Hypothesis testing", "Correlation vs causation"]},
        {"week": 6, "title": "Excel Mastery",          "tasks": ["PivotTables", "VLOOKUP / XLOOKUP", "Advanced charting"]},
        {"week": 7, "title": "Real-World Datasets",    "tasks": ["Analyse a public dataset", "Write an insights report", "Present findings"]},
        {"week": 8, "title": "Portfolio Project",      "tasks": ["End-to-end analysis project", "Publish on Kaggle/GitHub", "Prepare a deck"]}
    ]
}

# ── AI Assistant Responses (Rule-Based) ───────────────────────────────────

ASSISTANT_RESPONSES = {
    "resume": [
        "Keep your resume to 1-2 pages. Recruiters spend an average of 7 seconds scanning it.",
        "Use strong action verbs: built, designed, optimised, led, reduced, increased.",
        "Quantify your achievements wherever possible — e.g. 'Reduced page load time by 40%'.",
        "Tailor your resume keywords to each job description to pass ATS filters.",
        "Put your most impressive experience or project near the top of each section."
    ],
    "interview": [
        "Use the STAR method (Situation, Task, Action, Result) for behavioural questions.",
        "Research the company's products, values, and recent news before the interview.",
        "Prepare 2-3 questions to ask your interviewer — it shows genuine interest.",
        "Practice coding problems on LeetCode or HackerRank for technical rounds.",
        "Record yourself answering questions to spot filler words and improve delivery."
    ],
    "skills": [
        "Focus on depth over breadth — be exceptional at 2-3 core skills rather than mediocre at 10.",
        "Build real projects and deploy them publicly; they speak louder than certificates.",
        "Contribute to open-source projects to build a public portfolio and network.",
        "Write about what you learn — blog posts or LinkedIn articles establish credibility.",
        "Join communities (Discord servers, meetups, Reddit) to learn from peers."
    ],
    "career": [
        "Set clear 6-month and 1-year career goals to guide your skill investments.",
        "LinkedIn is essential — keep your profile updated and engage with content in your field.",
        "Networking accounts for up to 85% of jobs filled. Talk to people, not just job boards.",
        "Ask for feedback after rejections — it is rare but very valuable data.",
        "Consider a T-shaped skill profile: broad general knowledge with deep expertise in one area."
    ],
    "default": [
        "I am your AI Career Copilot! Ask me about resumes, interviews, skills, or career paths.",
        "Try asking: 'How do I improve my resume?' or 'How should I prepare for interviews?'",
        "Upload your resume above to get a personalised ATS score and skill gap analysis.",
        "I can help you build a learning roadmap tailored to your target role."
    ]
}

def get_assistant_response(message: str) -> str:
    """Rule-based career assistant."""
    import random
    msg = message.lower()
    if any(w in msg for w in ["resume", "cv", "ats", "format"]):
        category = "resume"
    elif any(w in msg for w in ["interview", "question", "hr", "technical"]):
        category = "interview"
    elif any(w in msg for w in ["skill", "learn", "course", "technology"]):
        category = "skills"
    elif any(w in msg for w in ["career", "job", "salary", "role", "switch"]):
        category = "career"
    else:
        category = "default"
    return random.choice(ASSISTANT_RESPONSES[category])

# ── PDF Extraction ─────────────────────────────────────────────────────────

def extract_text_from_pdf(file_stream) -> str:
    reader = PyPDF2.PdfReader(file_stream)
    return "".join(page.extract_text() or "" for page in reader.pages)

# ── Resume Parser (Regex-based) ────────────────────────────────────────────

def parse_resume(text: str) -> dict:
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Name — first short line without email/phone characters
    name = ""
    for line in lines[:5]:
        if not re.search(r'[@\d]', line) and len(line.split()) <= 5:
            name = line
            break

    # Email
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
    email = email_match.group(0) if email_match else ""

    # Phone
    phone_match = re.search(r'(\+?\d[\d\s\-().]{8,})', text)
    phone = phone_match.group(0).strip() if phone_match else ""

    # Skills
    skills = []
    skills_match = re.search(
        r'(?i)skills?[:\s]*(.*?)(?=\n[A-Z][A-Z\s]{2,}[:\n]|\Z)', text, re.DOTALL)
    if skills_match:
        raw = skills_match.group(1)
        skills = [s.strip() for s in re.split(r'[,|•\n]', raw) if 2 < len(s.strip()) < 40]
        skills = skills[:20]

    # Education
    education = []
    edu_match = re.search(
        r'(?i)education[:\s]*(.*?)(?=\n[A-Z][A-Z\s]{2,}[:\n]|\Z)', text, re.DOTALL)
    if edu_match:
        education = [l.strip() for l in edu_match.group(1).split('\n') if l.strip()][:4]

    # Experience
    experience = []
    exp_match = re.search(
        r'(?i)(?:work\s+)?experience[:\s]*(.*?)(?=\n[A-Z][A-Z\s]{2,}[:\n]|\Z)', text, re.DOTALL)
    if exp_match:
        experience = [l.strip() for l in exp_match.group(1).split('\n') if l.strip()][:6]

    # Projects
    projects = []
    proj_match = re.search(
        r'(?i)projects?[:\s]*(.*?)(?=\n[A-Z][A-Z\s]{2,}[:\n]|\Z)', text, re.DOTALL)
    if proj_match:
        projects = [l.strip() for l in proj_match.group(1).split('\n') if l.strip()][:6]

    # Certifications
    certs = []
    cert_match = re.search(
        r'(?i)certifications?[:\s]*(.*?)(?=\n[A-Z][A-Z\s]{2,}[:\n]|\Z)', text, re.DOTALL)
    if cert_match:
        certs = [l.strip() for l in cert_match.group(1).split('\n') if l.strip()][:5]

    # Links
    github   = re.search(r'github\.com/[\w-]+',   text, re.IGNORECASE)
    linkedin = re.search(r'linkedin\.com/in/[\w-]+', text, re.IGNORECASE)

    return {
        "name":           name,
        "email":          email,
        "phone":          phone,
        "skills":         skills,
        "education":      education,
        "experience":     experience,
        "projects":       projects,
        "certifications": certs,
        "github":         github.group(0)   if github   else "",
        "linkedin":       linkedin.group(0) if linkedin else ""
    }

# ── ATS Scorer ─────────────────────────────────────────────────────────────

def calculate_ats_score(parsed: dict) -> dict:
    score = 0
    strengths    = []
    improvements = []

    checks = [
        ("name",           10, "Name / Contact Info"),
        ("email",           8, "Email Address"),
        ("phone",           7, "Phone Number"),
        ("skills",         20, "Skills Section"),
        ("education",      15, "Education Section"),
        ("experience",     15, "Work Experience"),
        ("projects",       10, "Projects Section"),
        ("certifications",  5, "Certifications"),
        ("github",          5, "GitHub Profile"),
        ("linkedin",        5, "LinkedIn Profile"),
    ]

    for field, points, label in checks:
        value = parsed.get(field)
        has_value = (isinstance(value, list) and len(value) > 0) or \
                    (isinstance(value, str)  and value.strip())
        if has_value:
            score += points
            strengths.append(label)
        else:
            improvements.append(label)

    return {
        "score":        min(score, 100),
        "strengths":    strengths,
        "improvements": improvements,
        "summary":      f"Your resume scored {min(score,100)}/100. Focus on the improvements listed below."
    }

# ── Skill Gap ──────────────────────────────────────────────────────────────

def skill_gap_analysis(skills: list, target_role: str) -> dict:
    required          = ROLE_SKILLS.get(target_role, [])
    resume_lower      = [s.lower() for s in skills]

    found   = []
    missing = []
    for req in required:
        matched = any(req in rs or rs in req for rs in resume_lower)
        if matched:
            found.append(req.title())
        else:
            missing.append(req.title())

    pct = round(len(found) / len(required) * 100) if required else 0
    return {
        "found":            found,
        "missing":          missing,
        "match_percentage": pct,
        "role":             target_role,
        "verdict":          f"You match {pct}% of the required skills for {target_role}."
    }

# ── Interview Questions ────────────────────────────────────────────────────

def generate_interview_questions(skills: list) -> dict:
    questions = {"beginner": [], "intermediate": [], "advanced": []}
    skills_lower = [s.lower() for s in skills]
    used_keys    = set()

    for skill in skills_lower:
        for key in INTERVIEW_QUESTIONS:
            if key not in used_keys and (key in skill or skill in key):
                qs = INTERVIEW_QUESTIONS[key]
                questions["beginner"].extend(qs["beginner"])
                questions["intermediate"].extend(qs["intermediate"])
                questions["advanced"].extend(qs["advanced"])
                used_keys.add(key)
                break

    for level in ["beginner", "intermediate", "advanced"]:
        if len(questions[level]) < 5:
            questions[level].extend(GENERIC_QUESTIONS[level])
        questions[level] = list(dict.fromkeys(questions[level]))[:8]

    return questions

# ── Roadmap ────────────────────────────────────────────────────────────────

def generate_roadmap(target_role: str, missing_skills: list) -> list:
    base = ROADMAPS.get(target_role, ROADMAPS["Software Developer"])
    if missing_skills:
        priority = {
            "week":  0,
            "title": "Priority Skill Gaps",
            "tasks": [f"Study {s}" for s in missing_skills[:4]]
        }
        return [priority] + base
    return base

# ── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', api_configured=True)


@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['resume']
    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400

    try:
        text   = extract_text_from_pdf(BytesIO(file.read()))
        if not text.strip():
            return jsonify({"error": "Could not extract text. Please use a text-based PDF."}), 400

        parsed = parse_resume(text)
        ats    = calculate_ats_score(parsed)
        return jsonify({"success": True, "parsed": parsed, "ats": ats})

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@app.route('/skill-gap', methods=['POST'])
def skill_gap():
    data = request.get_json()
    return jsonify(skill_gap_analysis(
        data.get('skills', []),
        data.get('role', 'Software Developer')
    ))


@app.route('/interview-questions', methods=['POST'])
def interview_questions():
    data = request.get_json()
    return jsonify(generate_interview_questions(data.get('skills', [])))


@app.route('/roadmap', methods=['POST'])
def roadmap():
    data = request.get_json()
    return jsonify(generate_roadmap(
        data.get('role', 'Software Developer'),
        data.get('missing_skills', [])
    ))


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    return jsonify({"response": get_assistant_response(data.get('message', ''))})


@app.route('/download-report', methods=['POST'])
def download_report():
    data         = request.get_json()
    parsed       = data.get('parsed', {})
    ats          = data.get('ats', {})
    skill_gap    = data.get('skill_gap', {})
    questions    = data.get('questions', {})
    roadmap_data = data.get('roadmap', [])

    lines = [
        "=" * 62,
        "        AI CAREER COPILOT — ANALYSIS REPORT",
        "=" * 62, "",
        "── ATS SCORE ─────────────────────────────────────────────",
        f"  Score   : {ats.get('score', 'N/A')} / 100",
        f"  Summary : {ats.get('summary', '')}",
        "", "  Strengths:",
        *[f"    ✓ {s}" for s in ats.get('strengths', [])],
        "", "  Improvements Needed:",
        *[f"    ✗ {s}" for s in ats.get('improvements', [])],
        "",
        "── RESUME OVERVIEW ───────────────────────────────────────",
        f"  Name     : {parsed.get('name',     'N/A')}",
        f"  Email    : {parsed.get('email',    'N/A')}",
        f"  Phone    : {parsed.get('phone',    'N/A')}",
        f"  GitHub   : {parsed.get('github',   'N/A')}",
        f"  LinkedIn : {parsed.get('linkedin', 'N/A')}",
        "", "  Skills:",
        *[f"    • {s}" for s in parsed.get('skills', [])],
        "", "  Education:",
        *[f"    • {e}" for e in parsed.get('education', [])],
        "", "  Experience:",
        *[f"    • {e}" for e in parsed.get('experience', [])],
        "",
        "── SKILL GAP ANALYSIS ────────────────────────────────────",
        f"  Target Role : {skill_gap.get('role', 'N/A')}",
        f"  Match       : {skill_gap.get('match_percentage', 'N/A')}%",
        f"  Verdict     : {skill_gap.get('verdict', '')}",
        "", "  Skills You Have:",
        *[f"    ✓ {s}" for s in skill_gap.get('found', [])],
        "", "  Skills to Learn:",
        *[f"    ✗ {s}" for s in skill_gap.get('missing', [])],
        "",
        "── INTERVIEW QUESTIONS ───────────────────────────────────",
    ]

    for level in ["beginner", "intermediate", "advanced"]:
        lines.append(f"\n  {level.upper()}:")
        for q in questions.get(level, []):
            lines.append(f"    Q: {q}")

    lines += ["", "── LEARNING ROADMAP ──────────────────────────────────────"]
    for step in roadmap_data:
        lines.append(f"\n  Week {step.get('week','?')}: {step.get('title','')}")
        for task in step.get('tasks', []):
            lines.append(f"    → {task}")

    lines += [
        "", "=" * 62,
        "  Generated by AI Career Copilot",
        "=" * 62,
    ]

    buf = BytesIO("\n".join(lines).encode("utf-8"))
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name="career_report.txt",
                     mimetype="text/plain")


if __name__ == '__main__':
    app.run(debug=True, port=5000)