"""
Stage 4 — Feedback Generator
Reads graded_output.json, generates structured feedback per question using Gemini.
Includes retry logic for rate limiting.
"""

import os
import json
import re
import time
import requests
from dotenv import load_dotenv

# Try loading from the root .env first
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(root_env):
    load_dotenv(root_env)
else:
    # Fallback to stage1_extraction/.env
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "stage1_extraction", ".env"))
    # Generic load_dotenv searching current & parent directories
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL     = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key=" + (GEMINI_API_KEY or "")
)

MAX_RETRIES  = 3
RETRY_DELAY  = 60   # seconds to wait on 429


def call_gemini(prompt: str) -> str:
    """Calls Gemini with retry on rate limit."""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for attempt in range(MAX_RETRIES):
        response = requests.post(GEMINI_URL, json=payload)

        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        if response.status_code == 429:
            wait = RETRY_DELAY * (attempt + 1)
            print(f"\n  Rate limited - waiting {wait}s before retry {attempt+1}/{MAX_RETRIES}...")
            time.sleep(wait)
            continue

        raise Exception(f"Gemini error {response.status_code}: {response.text}")

    raise Exception(f"Gemini rate limit exceeded after {MAX_RETRIES} retries")


def generate_feedback(
    question:        str,
    expected_answer: str,
    student_answer:  str,
    score:           float,
    max_marks:       int
) -> dict:
    if not student_answer or not student_answer.strip():
        return {
            "correct":  "No answer provided.",
            "missing":  "Complete answer was expected.",
            "tip":      "Attempt all questions — partial credit is possible.",
            "summary":  "No answer submitted."
        }

    percentage = round((score / max_marks) * 100) if max_marks else 0

    prompt = f"""You are an academic teacher giving feedback on a student's answer.

Question: {question}
Expected answer: {expected_answer}
Student's answer: {student_answer}
Score awarded: {score} / {max_marks} ({percentage}%)

Give concise, constructive feedback. Be specific about what was right and wrong.
Do NOT repeat the full expected answer. Be encouraging but honest.

Return ONLY this JSON, no markdown, no explanation:
{{
  "correct": "what the student got right (1-2 sentences)",
  "missing": "what key points were missing or wrong (1-2 sentences)",
  "tip": "one specific tip to improve this answer next time",
  "summary": "one line overall assessment"
}}"""

    raw = call_gemini(prompt)
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


def generate_all_feedback(
    graded_output_path: str,
    final_output_path:  str,
    only_incorrect:     bool = False
) -> dict:
    with open(graded_output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Student  : {data['student_name']}")
    print(f"Score    : {data['total_scored']} / {data['total_marks']}")
    print(f"Questions: {data['num_questions']}")
    print()

    for i, question in enumerate(data["questions"]):
        qnum      = question["q_number"]
        score     = question.get("score") or 0
        max_marks = question["max_marks"]
        perfect   = score >= max_marks

        if only_incorrect and perfect:
            question["feedback"] = {
                "correct":  "Perfect answer — all key points covered.",
                "missing":  "Nothing.",
                "tip":      "Keep it up!",
                "summary":  "Full marks awarded."
            }
            print(f"  {qnum} [{score}/{max_marks}] -> skipped (full marks)")
            continue

        print(f"  {qnum} [{score}/{max_marks}] generating feedback...", end=" ", flush=True)

        try:
            feedback = generate_feedback(
                question        = question["question_text"],
                expected_answer = question["expected_answer"],
                student_answer  = question["student_answer"],
                score           = score,
                max_marks       = max_marks
            )
            question["feedback"] = feedback
            data["questions"][i] = question
            print(f"SUCCESS - {feedback['summary'][:60]}")
        except Exception as e:
            print(f"FAILED - {e}")
            question["feedback"] = {
                "correct":  "",
                "missing":  "",
                "tip":      "",
                "summary":  f"Feedback generation failed: {str(e)}"
            }

        # delay between calls to avoid rate limiting
        time.sleep(3)

    data["feedback_summary"] = {
        "total_questions":  data["num_questions"],
        "answered":         len([q for q in data["questions"] if q.get("student_answer", "").strip()]),
        "unanswered":       len([q for q in data["questions"] if not q.get("student_answer", "").strip()]),
        "total_scored":     data["total_scored"],
        "total_marks":      data["total_marks"],
        "percentage":       data.get("percentage", 0),
        "overall_remark":   get_overall_remark(data.get("percentage", 0))
    }

    with open(final_output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print()
    print(f"Overall  : {data['feedback_summary']['overall_remark']}")
    print(f"Saved to : {final_output_path}")
    return data


def get_overall_remark(percentage: float) -> str:
    if percentage >= 90:
        return "Outstanding performance."
    elif percentage >= 75:
        return "Good performance. Minor gaps to address."
    elif percentage >= 60:
        return "Satisfactory. Several concepts need revision."
    elif percentage >= 40:
        return "Below average. Significant revision needed."
    else:
        return "Poor performance. Thorough revision of all topics required."


if __name__ == "__main__":
    generate_all_feedback(
        graded_output_path = os.path.join("outputs", "graded_output.json"),
        final_output_path  = os.path.join("outputs", "final_output.json"),
        only_incorrect     = False
    )