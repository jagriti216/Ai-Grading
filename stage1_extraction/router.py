import os
import json
from stage1_extraction.pdf_extractor import extract_typed_pdf, is_typed_pdf
from stage1_extraction.ocr_extractor import extract_handwritten_pdf


INPUT_FILES = {
    "question_paper": ["question_paper.pdf"],
    "answer_key": ["answer_key.pdf"],
    "student_answer": ["student_answer.pdf", "student_solution.pdf"],
}


OUTPUT_FILES = {
    "question_paper.pdf": "question_paper_extracted.json",
    "answer_key.pdf": "answer_key_extracted.json",
    "student_answer.pdf": "student_answer_extracted.json",
    "student_solution.pdf": "student_answer_extracted.json",
}


def resolve_input_path(folder_path: str, candidates: list[str]) -> str | None:
    for candidate in candidates:
        candidate_path = os.path.join(folder_path, candidate)
        if os.path.exists(candidate_path):
            return candidate_path
    return None


def extract_pdf(pdf_path: str) -> dict:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    if not pdf_path.lower().endswith(".pdf"):
        raise ValueError(f"File must be a PDF: {pdf_path}")

    print(f"\nProcessing: {os.path.basename(pdf_path)}")

    typed = is_typed_pdf(pdf_path)
    pdf_type = "typed" if typed else "scanned/handwritten"
    print(f"  Detected as: {pdf_type}")

    pages = extract_typed_pdf(pdf_path) if typed else extract_handwritten_pdf(pdf_path)

    full_text = "\n\n".join(text for text in pages.values() if text.strip())

    return {
        "pdf_type":  pdf_type,
        "pdf_path":  pdf_path,
        "num_pages": len(pages),
        "pages":     pages,
        "full_text": full_text
    }


def extract_all_from_folder(folder_path: str) -> list:
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"No PDFs found in {folder_path}")
        return []

    results = []
    for fname in sorted(pdf_files):
        full_path = os.path.join(folder_path, fname)
        try:
            result = extract_pdf(full_path)
            results.append(result)
        except Exception as e:
            print(f"  Error processing {fname}: {e}")
            results.append({"pdf_path": full_path, "error": str(e)})

    return results


if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)

    for label, candidates in INPUT_FILES.items():
        path = resolve_input_path("uploads", candidates)
        if not path:
            print(f"Not found: {', '.join(candidates)} — skipping")
            continue
        try:
            r = extract_pdf(path)

            # save full output to JSON
            out_name = OUTPUT_FILES.get(os.path.basename(r["pdf_path"]), os.path.basename(r["pdf_path"]).replace(".pdf", "_extracted.json"))
            out_path = os.path.join("outputs", out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(r, f, indent=2, ensure_ascii=False)

            print("\n" + "=" * 60)
            print(f"File    : {os.path.basename(r['pdf_path'])}")
            print(f"Type    : {r['pdf_type']}")
            print(f"Pages   : {r['num_pages']}")
            print(f"Saved   : {out_path}")
            print(f"Preview :\n{r['full_text'][:600]}")
        except Exception as e:
            print(f"FAILED : {path} — {e}")
