import re
import os
import json
from stage2_parser.gemini_client import call_gemini_json_array, split_blocks_by_question


def _normalize_q_number(value: str) -> str:
    text = str(value).strip().upper()
    match = re.search(r"(\d+)", text)
    return f"Q{match.group(1)}" if match else text


def _ordered_page_texts(data: dict) -> list[str]:
    pages = data.get("pages", {})
    ordered = []
    for key in sorted(pages.keys(), key=lambda name: int(re.search(r"(\d+)$", name).group(1)) if re.search(r"(\d+)$", name) else 0):
        ordered.append(pages.get(key, "") or "")
    return ordered


def _detect_header(line: str) -> str | None:
    match = re.match(r"^\s*(?:q\s*)?(\d{1,3})\s*\)", line, flags=re.IGNORECASE)
    if not match:
        return None
    return f"Q{match.group(1)}"


def _extract_answers_from_pages(data: dict, question_numbers: list) -> list:
    question_order = [_normalize_q_number(q) for q in question_numbers]
    answer_map = {q: "" for q in question_order}
    pages = _ordered_page_texts(data)

    current_q = None
    seen_blocks = 0

    for page_text in pages:
        lines = page_text.splitlines()
        page_headers = []

        for line in lines:
            header = _detect_header(line)
            if header:
                page_headers.append((header, line.strip()))

        if page_headers:
            for idx, (header, line_text) in enumerate(page_headers):
                if header not in answer_map:
                    if seen_blocks == 0 and question_order:
                        header = question_order[0]
                    else:
                        continue

                start_index = next(i for i, line in enumerate(lines) if line.strip() == line_text)
                end_index = len(lines)
                if idx + 1 < len(page_headers):
                    next_line_text = page_headers[idx + 1][1]
                    for j in range(start_index + 1, len(lines)):
                        if lines[j].strip() == next_line_text:
                            end_index = j
                            break

                block_lines = [lines[start_index].strip()] + [ln.rstrip() for ln in lines[start_index + 1 : end_index] if ln.strip()]
                block_text = "\n".join(block_lines).strip()
                if block_text and not answer_map.get(header, ""):
                    answer_map[header] = block_text
                    current_q = header
                    seen_blocks += 1
        elif current_q and page_text.strip():
            answer_map[current_q] = (answer_map[current_q] + "\n" + page_text.strip()).strip()

    return [{"q_number": q, "answer_text": answer_map.get(q, "")} for q in question_order]


def _fallback_answer_parse(full_text: str, question_numbers: list) -> list:
    answer_map = {_normalize_q_number(q): "" for q in question_numbers}
    for q_num, block in split_blocks_by_question(full_text):
        q_key = f"Q{q_num}"
        if q_key not in answer_map:
            continue
        cleaned = block.strip()
        if cleaned and not answer_map[q_key]:
            answer_map[q_key] = cleaned
    return [{"q_number": q, "answer_text": answer_map[_normalize_q_number(q)]} for q in question_numbers]


def parse_answer_sheet(extracted_json_path: str, question_numbers: list) -> dict:
    with open(extracted_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    full_text = data["full_text"]
    q_list = ", ".join(question_numbers)

    prompt = f"""
You are a student answer sheet parser. The text below is a student's answer sheet.

Split the text into separate answers for these questions: {q_list}

Return a JSON array where each item has:
- "q_number": question number as string e.g. "Q1", "Q2"
- "answer_text": complete answer text the student wrote for that question including any code

Rules:
- Include ALL text the student wrote for each question, do not truncate
- Preserve code snippets exactly as written
- If a question has no answer, set answer_text to ""
- Return ONLY a valid JSON array, no explanation, no markdown backticks

Student answer sheet:
{full_text}
"""

    local_answers = _extract_answers_from_pages(data, question_numbers)

    if any(a["answer_text"].strip() for a in local_answers):
        answers = local_answers
    else:
        answers = call_gemini_json_array(
            prompt=prompt,
            fallback_builder=lambda: _fallback_answer_parse(full_text, question_numbers),
        )

    return {
        "source_file": data["pdf_path"],
        "num_answers": len([a for a in answers if a["answer_text"].strip()]),
        "answers":     answers
    }


if __name__ == "__main__":
    answer_path = os.path.join("outputs", "student_answer_extracted.json")
    qp_path     = os.path.join("outputs", "question_paper_parsed.json")

    if os.path.exists(qp_path):
        with open(qp_path, "r", encoding="utf-8") as f:
            qp = json.load(f)
        q_numbers = [q["q_number"] for q in qp["questions"]]
    else:
        q_numbers = ["Q1", "Q2", "Q3", "Q4"]

    result = parse_answer_sheet(answer_path, q_numbers)
    out = os.path.join("outputs", "answer_sheet_parsed.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Parsed {result['num_answers']} student answers")
    print(f"Saved to {out}")
