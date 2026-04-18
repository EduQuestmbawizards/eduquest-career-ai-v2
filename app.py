from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# ✅ OpenAI client
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
                <p>
                Try inputs like:<br>
                • I want to become a doctor<br>
                • I want to become an engineer<br>
                • I want to go into business
                </p>
            </div>
            """
        })

    prompt = f"""[YOUR SAME PROMPT HERE]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        output = response.choices[0].message.content.strip()

        if (
            not output
            or "<h2>" not in output
            or "<ul>" not in output
            or "```" in output
        ):
            raise ValueError("Invalid output")

        return jsonify({"result": output})

    except Exception as e:
        print("ERROR:", str(e))  # 👈 logs for Render

        return jsonify({
            "result": """
            <div style="padding:20px;">
                <h2>⚠️ Unable to Generate Career Plan</h2>
                <p>Please try again later.</p>

                <h3>📞 Contact</h3>
                <p>
                Email: contact@eduquest.org.in<br>
                Phone: +91 9958041888
                </p>
            </div>
            """
        })


# 🔥 Render-ready run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)