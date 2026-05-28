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


ADDITIONAL INTELLIGENCE RULES:

For country-specific recommendations:

- Mention scholarship culture where relevant
- Mention whether universities evaluate students holistically
- Mention importance of research, leadership or extracurricular depth where applicable
- Mention what profile characteristics are commonly valued in that country
- Keep country insights concise and integrated naturally into the response

For every country automatically identify:

- admission style
- scholarship culture
- profile expectations
- competitiveness level

STRICT STRUCTURE (FOLLOW EXACTLY):

<h2>🏛️ Admissions Roadmap: {user_input}</h2>

<h3>🎓 Why This University Fits You</h3>
<p> Do Not give wikipedia description.

Explain:
- why this university matches THIS candidate
- what type of students the university seeks
- where candidate aligns
- where candidate currently falls short
- one unique positioning opportunity

Maximum: 150 words
</p>

<h3>📋 Entry Requirements & Competitive Exam Strategy</h3>
For the Entry Requirements & Competitive Exam Strategy section:

Format the response as a proper HTML unordered list.

Do NOT write labels like:
"Mandatory Exams:"
"Recommended Exams:"
"Optional Exams:"

Instead generate:

<ul>

<li><strong>Required Exams:</strong> Explain required exams and competitive score ranges.</li>

<li><strong>Recommended Exams:</strong> Explain optional exams that strengthen applications.</li>

<li><strong>English Proficiency:</strong> Mention IELTS/TOEFL where applicable.</li>

<li><strong>Scholarship Positioning:</strong> Explain how scores affect competitiveness.</li>

</ul>

Never output numbered instructions.


<h3>📊 Your Profile Assessment</h3>
<p>
Assess using:

Academic Strength:
Leadership Strength:
Technical Strength:
Exposure Strength:

Then identify:

Critical Gaps:
Differentiation Gap:
Narrative Gap:

Do not praise without evidence.
Think like admissions committee.
</p>

<h3>🧠 EduQuest Strategic Insight</h3>
Generate one high-value counseling insight:

Examples:

- Why students lose opportunities
- Why profile building matters
- Why grades alone are insufficient
- Why global competition changes admissions


<h3>🚀 Signature Work Development</h3>

<p>

Recommend ONE high-leverage flagship project.

Format:

Problem:
Execution:
Tools:
Expected outcome:
University value:
Career value:

Must align with student field.

</p>

<h3>📖 Building Your Narrative</h3>
<p>
Explain what makes a compelling personal narrative for this specific program.
What story should the student tell? What themes connect their background, passion, and future goals?
This is the core of what Narrative Architects specialises in.
</p>

<h3>🏆 Strategic Profile Building</h3>
For Strategic Profile Building:

Do NOT output framework instructions.

Instead convert the framework into natural advisory language.

Internally use:

Exploration → Skill Building → Differentiation → Narrative Building

but NEVER print these labels directly.

Generate 1–2 paragraphs explaining profile growth naturally.

Then provide 3–4 concise bullet recommendations.

Avoid implementation details.

<h3>🤖 AI & Data Science Relevance in Your Career Path</h3>
Explain:

- how AI and Data Science intersect with the student's chosen field
- future applications
- industry changes
- skills that become valuable

Keep practical and future-focused.


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


<h3>🛤️ Strategic Action Roadmap</h3>

<ul>

<li>Immediate Next Steps</li>

<li>Next 6 Months</li>

<li>Next 1 Year</li>

<li>Before Application Submission</li>

</ul>

<h3>🚀 Future Readiness & Career Positioning</h3>

Explain:

- future industry trends
- AI impact
- competitive skills
- long-term positioning

<h3>🎯 Strategic Positioning Statement</h3>

<p>

Generate one memorable statement under 20 words.

Examples:

"Technology-enabled healthcare leaders will define the next decade."

"Future finance leaders combine analytical depth with human judgment."

</p>

<p>
Your narrative should connect your academic journey, motivations and future ambitions into a coherent story rather than isolated achievements.
</p>

<p>
Strong narratives rarely emerge by accident. EduQuest helps students transform experiences into a clear and authentic identity aligned with university expectations.
</p>


<h3>📞 Begin Your Journey</h3>
<p>
Elite applications are rarely built accidentally. They are intentionally designed through strategy, positioning and long-term planning.

EduQuest helps students transform ambitions into globally competitive profiles.
</p>
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
            model="gpt-4o",
            messages=[
                {
                    "role":"system",
                    "content":"You are a senior university admissions strategist and profile architect. Think deeply before writing."
                },
                {
                    "role":"user",
                    "content":prompt
                }
            ],
            temperature=0.7
        )

        output = response.choices[0].message.content.strip()

        # Robustly clean markdown code block wrap if returned by the LLM
        if output.startswith("```"):
            lines = output.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            output = "\n".join(lines).strip()

        if not output or "<h2>" not in output or "<ul>" not in output:
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