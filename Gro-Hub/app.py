from flask import Flask, request, jsonify, render_template
import json
import pandas as pd
import pdfplumber
import docx
import warnings
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import os

warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)

# ==== Load datasets ====
with open("resume_dataset.json") as f:
    resume_data = json.load(f)
with open("role_skill_mapping.json") as f:
    role_data = json.load(f)
with open("learning_recommendations.json") as f:
    raw_course_data = json.load(f)

# ==== Normalize skill keys ====
def normalize_skill_key(skill):
    return skill.strip().replace("/", " ").title()
course_data = {normalize_skill_key(k): v for k, v in raw_course_data.items()}

# ==== Train model ====
df = pd.DataFrame(resume_data)
vectorizer = TfidfVectorizer(stop_words="english", max_features=3000)
X, y = vectorizer.fit_transform(df["resume_text"]), df["label"]
model = MultinomialNB().fit(X, y)

# ==== File extract functions ====
def extract_text_from_pdf(fp):
    text = ""
    with pdfplumber.open(fp) as pdf:
        for p in pdf.pages:
            t = p.extract_text()
            if t: text += t + "\n"
    return text.strip()

def extract_text_from_docx(fp):
    return "\n".join(p.text for p in docx.Document(fp).paragraphs).strip()

def extract_skills(text):
    return {w.strip(".,()").lower() for w in text.split() if w and w[0].isupper()}

def get_required_skills(role_title):
    for r in role_data:
        if r["Job Role"].lower() == role_title.lower():
            return [s.strip().lower() for s in r["Skills Required"].split(",")]
    return []

def get_course_recommendations(missing_skills):
    recs = []
    for skill in missing_skills:
        key = normalize_skill_key(skill)
        for c in course_data.get(key, []):
            recs.append({
                "skill": key,
                "course": c["course"],
                "platform": c["platform"],
                "link": c["link"]
            })
    return recs

# ==== Routes ====
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    filepath = os.path.join("uploads", file.filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(filepath)

    # Extract text
    if filepath.endswith(".pdf"):
        text = extract_text_from_pdf(filepath)
    else:
        text = extract_text_from_docx(filepath)

    if not text:
        return jsonify({"error": "Could not extract text"}), 400

    # Predict roles
    probs = model.predict_proba(vectorizer.transform([text]))[0]
    roles = model.classes_
    top_idx = np.argsort(probs)[::-1][:5]  # Top 5 roles
    skills = extract_skills(text)

    results = []
    for idx in top_idx:
        role = roles[idx]
        conf = round(probs[idx] * 100, 1)
        req = set(get_required_skills(role))
        matched = sorted(skills & req)
        missing = sorted(req - skills)
        recs = get_course_recommendations(missing)
        results.append({
            "role": role,
            "confidence": conf,
            "matched_skills": matched,
            "missing_skills": missing,
            "recommended_courses": recs
        })

    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(debug=True)
