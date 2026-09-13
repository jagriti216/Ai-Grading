import re
import os
import json
from stage2_parser.gemini_client import (
    call_gemini_json_array,
    parse_marks_from_text,
    split_blocks_by_question,
)


def _fallback_question_parse(full_text: str) -> list:
    questions = []
    for q_num, block in split_blocks_by_question(full_text):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        question_text = "\n".join(lines)
        questions.append(
            {
                "q_number": f"Q{q_num}",
                "question_text": question_text,
                "max_marks": parse_marks_from_text(question_text),
            }
        )
    return questions


def parse_question_paper(extracted_json_path: str) -> dict:
    with open(extracted_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    full_text = data["full_text"]

    prompt = f"""
You are a question paper parser. Extract all questions from the text below.

Return a JSON array where each item has:
- "q_number": question number as string e.g. "Q1", "Q2"
- "question_text": full question text including any sub-parts or code snippets
- "max_marks": integer marks for that question (look for patterns like [4 Marks], 3+3 Marks etc. sum them if needed)

Rules:
- Include complete question text, do not truncate
- If marks written as 3+3, sum to 6
- If no marks found, set max_marks to null
- Return ONLY a valid JSON array, no explanation, no markdown backticks

Text:
{full_text}
"""

    questions = call_gemini_json_array(
        prompt=prompt,
        fallback_builder=lambda: _fallback_question_parse(full_text),
    )

    return {
        "source_file":   data["pdf_path"],
        "total_marks":   sum(q["max_marks"] for q in questions if q["max_marks"]),
        "num_questions": len(questions),
        "questions":     questions
    }


if __name__ == "__main__":
    path = os.path.join("outputs", "question_paper_extracted.json")
    result = parse_question_paper(path)
    out = os.path.join("outputs", "question_paper_parsed.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Parsed {result['num_questions']} questions, {result['total_marks']} total marks")
    print(f"Saved to {out}")
