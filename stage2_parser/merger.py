import os
import json
import re


def normalize_q_number(value: str) -> str:
    text = str(value).strip().upper()
    match = re.search(r"(\d+)", text)
    return f"Q{match.group(1)}" if match else text


def extract_student_name(extracted_json_path: str) -> str:
    """
    Try to extract student name from the answer sheet extracted JSON.
    Looks for common patterns like 'Name: ...' or 'Enrollment No.'
    """
    try:
        with open(extracted_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("full_text", "")
        match = re.search(r"Name[:\s]+([A-Za-z\s]+?)(?:\n|Enrollment)", text)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return "Unknown"


def merge(
    question_paper_parsed_path: str,
    answer_key_parsed_path: str,
    answer_sheet_parsed_path: str,
    student_answer_extracted_path: str
) -> dict:
    """
    Merges question paper, answer key, and student answers into
    one grading-ready object for Stage 3.
    """
    with open(question_paper_parsed_path, "r", encoding="utf-8") as f:
        qp = json.load(f)

    with open(answer_key_parsed_path, "r", encoding="utf-8") as f:
        ak = json.load(f)

    with open(answer_sheet_parsed_path, "r", encoding="utf-8") as f:
        ans = json.load(f)

    # index answer key and student answers by q_number for fast lookup
    ak_index = {
        normalize_q_number(a["q_number"]): a["expected_answer"]
        for a in ak["answer_key"]
    }
    ans_index = {
        normalize_q_number(a["q_number"]): a["answer_text"]
        for a in ans["answers"]
    }

    student_name = extract_student_name(student_answer_extracted_path)

    merged_questions = []
    for q in qp["questions"]:
        qnum = normalize_q_number(q["q_number"])
        merged_questions.append({
            "q_number":        qnum,
            "question_text":   q["question_text"],
            "expected_answer": ak_index.get(qnum, ""),
            "student_answer":  ans_index.get(qnum, ""),
            "max_marks":       q["max_marks"],
            "score":           None,   # filled by Stage 3
            "feedback":        None    # filled by Stage 3
        })

    return {
        "student_name":  student_name,
        "total_marks":   qp["total_marks"],
        "num_questions": qp["num_questions"],
        "questions":     merged_questions
    }


if __name__ == "__main__":
    result = merge(
        question_paper_parsed_path    = os.path.join("outputs", "question_paper_parsed.json"),
        answer_key_parsed_path        = os.path.join("outputs", "answer_key_parsed.json"),
        answer_sheet_parsed_path      = os.path.join("outputs", "answer_sheet_parsed.json"),
        student_answer_extracted_path = os.path.join("outputs", "student_answer_extracted.json")
    )

    out = os.path.join("outputs", "grading_ready.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Student      : {result['student_name']}")
    print(f"Total marks  : {result['total_marks']}")
    print(f"Questions    : {result['num_questions']}")
    print()
    for q in result["questions"]:
        has_answer = "✓" if q["student_answer"].strip() else "✗ no answer"
        has_key    = "✓" if q["expected_answer"].strip() else "✗ no key"
        print(f"{q['q_number']} [{q['max_marks']} marks] answer:{has_answer} key:{has_key}")
    print()
    print(f"Saved to {out}")
