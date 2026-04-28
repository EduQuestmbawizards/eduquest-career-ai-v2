from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    user_input = data.get("query", "").strip().lower()

    useless_inputs = ["hi", "hello", "hey", "how are you", "hii", "yo"]

    if not user_input or user_input in useless_inputs or len(user_input) < 5:
        return jsonify({
            "result": """
            <div>
                <h2>⚠️ Please Enter a Career Goal</h2>
                <p>Try inputs like:<br>
                • I want to become a doctor<br>
                • I want to become an engineer<br>
                • I want to go into business</p>
            </div>
            """
        })

    prompt = f"""
You are an expert career advisor and strategist working for EduQuest.

Your job is to generate a HIGHLY DETAILED, STRUCTURED, and PERSUASIVE career roadmap in HTML format.

User goal: {user_input}

CORE OBJECTIVE:
- Explain the career deeply (future scope, roadmap, salary, opportunities)
- Guide the student step-by-step on what to do
- Strongly integrate AI & Data Science as a MUST-HAVE skill
- Convince the student that learning AI/Data Science gives a major advantage
- Naturally promote EduQuest as the best way to achieve this

TONE:
- Professional, premium, intelligent
- Persuasive but NOT spammy
- Future-focused and practical

STRICT STRUCTURE (FOLLOW EXACTLY):

<h2>🚀 Career Roadmap: {user_input}</h2>

<h3>🌍 Career Overview</h3>
<p>Explain what this career is, what professionals do, and its future scope globally. Mention demand, growth, and industry trends.</p>

<h3>📈 Future Scope & Opportunities</h3>
<ul>
<li>Industry growth</li>
<li>Global demand</li>
<li>Emerging trends</li>
</ul>

<h3>💰 Salary Insights</h3>
<ul>
<li>Entry-level salary</li>
<li>Mid-level salary</li>
<li>Top-level earning potential</li>
<li>Global salary comparison</li>
</ul>

<h3>🛤️ Step-by-Step Roadmap</h3>
<ul>
<li>Step 1: Education</li>
<li>Step 2: Skills</li>
<li>Step 3: Projects</li>
<li>Step 4: Internships</li>
<li>Step 5: Career entry</li>
</ul>

<h3>🤖 Role of AI & Data Science</h3>
<p>Explain clearly how AI/Data Science is transforming this field. Explain why students without these skills will struggle in the future.</p>

<h3>🚀 Projects You Should Build</h3>
<ul>
<li>Project 1 (AI + career related)</li>
<li>Project 2</li>
<li>Project 3</li>
</ul>

<h3>🔥 Why You Should Learn AI & Data Science</h3>
<p>Convince the student strongly but professionally that combining this career with AI/Data Science creates a powerful advantage. Explain how it improves opportunities, salary, and global chances.</p>

<h3>📘 How EduQuest Helps You</h3>
<p>EduQuest provides a structured AI & Data Science program that focuses on real-world projects, research exposure, and career alignment. Instead of random learning, it builds a strong portfolio that helps students stand out in top universities and careers.</p>

<h3>📞 Get Guidance</h3>
<p>Email: contact@eduquest.org.in<br>Phone: +91 99580 41888</p>

RULES:
- Output ONLY HTML
- No markdown
- No backticks
- Keep content detailed and structured
- Maintain readability
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        output = response.choices[0].message.content.strip()

        if not output or "<h2>" not in output or "<ul>" not in output or "```" in output:
            raise ValueError("Invalid output")

        return jsonify({"result": output})

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "result": """
            <div style="padding:20px;">
                <h2>⚠️ Unable to Generate Career Plan</h2>
                <p>Please try again later.</p>
                <h3>📞 Contact</h3>
                <p>Email: contact@eduquest.org.in<br>Phone: +91 9958041888</p>
            </div>
            """
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)