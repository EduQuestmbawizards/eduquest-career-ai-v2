from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os
import json
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── In-memory store (swap for a DB in production) ──
student_profiles = {}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit-profile", methods=["POST"])
def submit_profile():
    """Receive and store the intake form data."""
    data = request.get_json(silent=True) or {}

    # Stamp and store
    data["submitted_at"] = datetime.utcnow().isoformat()
    email = data.get("email", "").strip().lower()
    if email:
        student_profiles[email] = data

    # ── Optional: log to a JSONL file so you never lose leads ──
    try:
        with open("leads.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        print("Lead log error:", e)

    return jsonify({"status": "ok"})


def build_profile_context(profile: dict) -> str:
    """Turn the student profile dict into a readable context block for the prompt."""
    if not profile:
        return ""

    lines = ["STUDENT PROFILE:"]

    def add(label, key):
        val = profile.get(key, "").strip() if isinstance(profile.get(key), str) else str(profile.get(key, ""))
        if val and val not in ("0", ""):
            lines.append(f"  • {label}: {val}")

    add("Name", "fullName")
    add("Age", "age")
    add("Email", "email")
    add("Phone", "phone")
    add("City", "city")
    add("Country", "country")
    add("Nationality", "nationality")
    add("Education Level", "educationLevel")
    add("Field of Study", "fieldOfStudy")
    add("CGPA / Percentage", "cgpa")
    add("Graduation Year", "graduationYear")
    add("Gap Years", "gapYears")
    add("Work Experience", "workExperience")
    add("Target Country", "targetCountry")
    add("Dream University", "dreamUniversity")
    add("Dream Course", "dreamCourse")

    # Scores (only if provided)
    scores = []
    for label, key in [("SAT", "satScore"), ("GMAT", "gmatScore"),
                        ("IELTS", "ieltsScore"), ("GRE", "greScore"), ("TOEFL", "toeflScore")]:
        v = str(profile.get(key, "")).strip()
        if v:
            scores.append(f"{label}: {v}")
    if scores:
        lines.append("  • Test Scores: " + ", ".join(scores))

    add("Additional Notes", "notes")

    return "\n".join(lines) if len(lines) > 1 else ""


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    user_input = (data.get("query") or "").strip()
    profile = data.get("profile") or {}

    useless = {"hi", "hello", "hey", "how are you", "hii", "yo"}
    if not user_input or user_input.lower() in useless or len(user_input) < 5:
        return jsonify({
            "result": """
            <div>
                <h2>Please Enter Your University Goal</h2>
                <p>Try inputs like:<br>
                • I want to study Medicine at Oxford<br>
                • I want to get into Harvard Law<br>
                • I want to study Computer Science at MIT</p>
            </div>
            """
        })

    profile_context = build_profile_context(profile)

    prompt = f"""
You are an elite university admissions strategist working for Narrative Architects — a premium consultancy that helps students gain admission to the world's top universities.

Your job is to generate a HIGHLY DETAILED, STRUCTURED, and COMPELLING university admissions roadmap in HTML format.

Student goal: {user_input}

{profile_context}

CORE OBJECTIVE:
- Craft a complete, personalised admissions strategy for this student
- Where a student profile is provided, tailor the advice specifically to their background, scores, education level, and nationality
- Explain what makes a strong application to this specific university/program
- Guide the student step-by-step on academics, extracurriculars, essays, and interviews
- Strongly integrate the role of a strong personal narrative
- Naturally promote Narrative Architects as the expert guide for this journey

TONE:
- Prestigious, intelligent, warm
- Aspirational but grounded and practical
- Like an Oxbridge tutor who genuinely wants you to succeed
- If you have the student's name, address them personally once or twice

STRICT STRUCTURE (FOLLOW EXACTLY):

<h2>🏛️ Admissions Roadmap: {user_input}</h2>

<h3>🎓 About This Program & University</h3>
<p>Explain the university, the program, its global reputation, what makes it special, and what kind of students it seeks. Be specific.</p>

<h3>📋 Entry Requirements</h3>
<ul>
<li>Academic grades / GPA / A-levels / IB requirements</li>
<li>Standardised test scores (SAT, ACT, LNAT, BMAT, UKCAT etc.) — if the student has scores, comment on how they compare</li>
<li>Subject prerequisites</li>
<li>Language requirements — reference the student's IELTS/TOEFL score if provided</li>
</ul>

<h3>📊 Your Profile Assessment</h3>
<p>
If a student profile was provided, give a candid but encouraging assessment of how their current academic standing, scores, and background position them for this application.
Point out strengths to build on and gaps to address. If no profile data is available, describe what a competitive applicant's profile looks like.
</p>

<h3>📖 Building Your Narrative</h3>
<p>
Explain what makes a compelling personal narrative for this specific program.
What story should the student tell? What themes connect their background, passion, and future goals?
This is the core of what Narrative Architects specialises in.
</p>

<h3>🏆 Extracurriculars & Profile Building</h3>
<ul>
<li>Research / internship / shadowing experience relevant to this program</li>
<li>Leadership roles, competitions, awards</li>
<li>Reading, projects, and intellectual engagement beyond school</li>
<li>Community impact and character-building activities</li>
</ul>

<h3>✍️ Personal Statement / Essay Strategy</h3>
<p>
Explain the personal statement or essay requirements for this university.
Give specific advice on what to include, what to avoid, and how to make it stand out.
Mention the narrative arc: hook, development, resolution, and future vision.
</p>

<h3>🗣️ Interview Preparation</h3>
<p>
If this university interviews (Oxford tutorials, Oxbridge, Harvard, etc.), explain what to expect.
Provide tips on how to prepare, what interviewers are looking for, and how to demonstrate intellectual curiosity.
</p>

<h3>🛤️ Year-by-Year Roadmap</h3>
<ul>
<li>Year 1-2 (Age 14-16): Foundation academics, reading widely, discovering passion</li>
<li>Year 3 (Age 16-17): Qualifications, first extracurriculars, early research</li>
<li>Year 4 (Age 17-18): Applications, personal statement, interview prep, final push</li>
</ul>

<h3>📘 How Narrative Architects Helps You</h3>
<p>
Narrative Architects provides elite, bespoke university admissions consulting. We specialise in helping students craft powerful personal narratives that resonate with admissions committees at Oxford, Cambridge, Harvard, MIT, LSE, and other world-leading institutions.
Our approach combines strategic academic planning with authentic storytelling — ensuring your application doesn't just meet requirements, but genuinely stands out.
</p>

<h3>📞 Begin Your Journey</h3>
<p>
Email: contact@eduquest.org.in<br>
Phone: +91 99580 41888
</p>

RULES:
- Output ONLY HTML
- No markdown
- No backticks
- Keep content detailed, structured and elegant
- Use specific university knowledge (actual requirements, actual interview formats)
- Maintain a premium, aspirational tone throughout
- Personalise using the student profile wherever possible
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        output = response.choices[0].message.content.strip()

        if not output or "<h2>" not in output or "<ul>" not in output or "```" in output:
            raise ValueError("Invalid output format")

        return jsonify({"result": output})

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "result": """
            <div style="padding:20px;">
                <h2>Unable to Generate Roadmap</h2>
                <p>Please try again later.</p>
                <h3>📞 Contact Narrative Architects</h3>
                <p>
                Email: contact@eduquest.org.in<br>
                Phone: +91 99580 41888
                </p>
            </div>
            """
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)