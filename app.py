from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv  # ← ADD THIS

# Load variables from .env file
load_dotenv()  # ← ADD THIS LINE

app = Flask(__name__, static_folder=".", template_folder=".")
CORS(app)

# This will now read from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/check", methods=["POST"])
def check_symptoms():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON input."}), 400

    symptoms = data.get("symptoms", "").strip()
    age = data.get("age")
    sex = data.get("sex", "").strip()

    # Validation
    if not symptoms:
        return jsonify({"error": "Symptoms are required."}), 400
    if not age:
        return jsonify({"error": "Age is required."}), 400
    if not sex:
        return jsonify({"error": "Sex is required."}), 400

    try:
        age = int(age)
        if age < 0 or age > 120:
            raise ValueError("Age must be between 0 and 120.")
    except (ValueError, TypeError):
        return jsonify({"error": "Please enter a valid age (0–120)."}), 400

    if sex not in ["male", "female", "other"]:
        return jsonify({"error": "Invalid sex selection."}), 400

    # Construct prompt
    prompt = f"""
    A patient reports the following symptoms: "{symptoms}".
    Age: {age}, Sex: {sex}.
    Provide 2–3 possible medical conditions in plain language.
    Then suggest general next steps (e.g., rest, hydration, see a doctor).
    Keep the response concise (under 150 words), calm, and non-alarming.
    Always emphasize: "This is not a diagnosis—consult a healthcare professional."
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.5
        )
        answer = response.choices[0].message.content.strip()

        return jsonify({
            "conditions": answer,
            "next_steps": "Consult a qualified healthcare provider for accurate diagnosis and care."
        })

    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"[ERROR] OpenAI API failed: {e}")
        return jsonify({
            "conditions": "We're temporarily unable to analyze your symptoms.",
            "next_steps": "Please try again later or contact a medical professional directly."
        }), 500

if __name__ == "__main__":
    app.run(debug=True)