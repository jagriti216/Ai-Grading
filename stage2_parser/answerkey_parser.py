import re
import os
import json
from stage2_parser.gemini_client import call_gemini_json_array, split_blocks_by_question


def _fallback_answerkey_parse(full_text: str) -> list:
    parsed = []
    for q_num, block in split_blocks_by_question(full_text):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        answer_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else lines[0]
        parsed.append({"q_number": f"Q{q_num}", "expected_answer": answer_text})
    return parsed


def _normalize_q_number(value) -> str:
    text = str(value).strip().upper()
    match = re.search(r"(\d+)", text)
    return f"Q{match.group(1)}" if match else text


def _load_question_order() -> list:
    qp_path = os.path.join("outputs", "question_paper_parsed.json")
    if not os.path.exists(qp_path):
        return []

    try:
        with open(qp_path, "r", encoding="utf-8") as f:
            qp = json.load(f)
        return [_normalize_q_number(q.get("q_number", "")) for q in qp.get("questions", [])]
    except Exception:
        return []


def _sanitize_answers(model_answers: list, fallback_answers: list, ordered_qnums: list) -> list:
    fallback_index = {
        _normalize_q_number(a.get("q_number", "")): a.get("expected_answer", "").strip()
        for a in fallback_answers
        if isinstance(a, dict)
    }

    cleaned_index = {}
    for item in model_answers:
        if not isinstance(item, dict):
            continue
        qnum = _normalize_q_number(item.get("q_number", ""))
        if not qnum:
            continue
        expected = str(item.get("expected_answer", "")).strip()
        if not expected:
            expected = fallback_index.get(qnum, "")
        cleaned_index[qnum] = expected

    for qnum, expected in fallback_index.items():
        if qnum not in cleaned_index or not cleaned_index[qnum]:
            cleaned_index[qnum] = expected

    if ordered_qnums:
        ordered = []
        seen = set()
        for qnum in ordered_qnums:
            if qnum in cleaned_index:
                ordered.append({"q_number": qnum, "expected_answer": cleaned_index[qnum]})
                seen.add(qnum)
        for qnum in sorted(cleaned_index.keys(), key=lambda x: int(re.search(r"\d+", x).group())):
            if qnum not in seen:
                ordered.append({"q_number": qnum, "expected_answer": cleaned_index[qnum]})
        return ordered

    return [
        {"q_number": qnum, "expected_answer": cleaned_index[qnum]}
        for qnum in sorted(cleaned_index.keys(), key=lambda x: int(re.search(r"\d+", x).group()))
    ]


def parse_answer_key(extracted_json_path: str) -> dict:
    with open(extracted_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    full_text = data["full_text"]

    prompt = f"""
You are an answer key parser. Extract the model answer for each question from the text below.

Return a JSON array where each item has:
- "q_number": question number as string e.g. "Q1", "Q2"
- "expected_answer": complete model answer text for that question including any code, diagrams described, formulas, or key points

Rules:
- Include ALL content of the expected answer, do not summarize or truncate
- Preserve code snippets, formulas, bullet points exactly as written
- If a question has multiple parts, include all parts in expected_answer
- Return ONLY a valid JSON array, no explanation, no markdown backticks

Text:
{full_text}
"""

    fallback_answers = _fallback_answerkey_parse(full_text)
    ordered_qnums = _load_question_order()

    model_answers = call_gemini_json_array(
        prompt=prompt,
        fallback_builder=lambda: fallback_answers,
    )
    answers = _sanitize_answers(model_answers, fallback_answers, ordered_qnums)

    return {
        "source_file": data["pdf_path"],
        "num_answers": len(answers),
        "answer_key":  answers
    }


if __name__ == "__main__":
    path = os.path.join("outputs", "answer_key_extracted.json")
    result = parse_answer_key(path)
    out = os.path.join("outputs", "answer_key_parsed.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Parsed {result['num_answers']} answer key entries")
    print(f"Saved to {out}")
