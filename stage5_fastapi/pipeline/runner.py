"""
Pipeline runner — calls Stage 1 → 2 → 3 → 4 in sequence.
Takes file paths, returns final graded output dict.
"""

import logging
import os
import json
from stage1_extraction.router          import extract_pdf
from stage2_parser.question_parser     import parse_question_paper
from stage2_parser.answerkey_parser    import parse_answer_key
from stage2_parser.answer_parser       import parse_answer_sheet
from stage2_parser.merger              import merge
from stage3_grading.grader             import grade_all
from stage4_feedback.feedback_generator import generate_all_feedback

logger = logging.getLogger(__name__)


def run_pipeline(
    question_paper_path: str,
    answer_key_path:     str,
    student_answer_path: str,
    output_dir:          str
) -> dict:
    """
    Runs the full grading pipeline end to end.

    Args:
        question_paper_path: path to question paper PDF
        answer_key_path:     path to answer key PDF
        student_answer_path: path to student answer PDF
        output_dir:          directory to save intermediate JSONs

    Returns:
        final graded output dict with scores and feedback
    """
    os.makedirs(output_dir, exist_ok=True)

    # ── Stage 1: OCR extraction ───────────────────────────────────────────
    logger.info("Stage 1: Extracting text from PDFs...")

    qp_extracted  = extract_pdf(question_paper_path)
    ak_extracted  = extract_pdf(answer_key_path)
    ans_extracted = extract_pdf(student_answer_path)

    qp_path  = os.path.join(output_dir, "qp_extracted.json")
    ak_path  = os.path.join(output_dir, "ak_extracted.json")
    ans_path = os.path.join(output_dir, "ans_extracted.json")

    with open(qp_path,  "w", encoding="utf-8") as f: json.dump(qp_extracted,  f, indent=2)
    with open(ak_path,  "w", encoding="utf-8") as f: json.dump(ak_extracted,  f, indent=2)
    with open(ans_path, "w", encoding="utf-8") as f: json.dump(ans_extracted, f, indent=2)

    logger.info("Stage 1 complete")

    # ── Stage 2: Parsing ──────────────────────────────────────────────────
    logger.info("Stage 2: Parsing structured data...")

    qp_parsed  = parse_question_paper(qp_path)
    ak_parsed  = parse_answer_key(ak_path)
    ans_parsed = parse_answer_sheet(
        ans_path,
        [q["q_number"] for q in qp_parsed["questions"]]
    )

    qp_parsed_path  = os.path.join(output_dir, "qp_parsed.json")
    ak_parsed_path  = os.path.join(output_dir, "ak_parsed.json")
    ans_parsed_path = os.path.join(output_dir, "ans_parsed.json")

    with open(qp_parsed_path,  "w", encoding="utf-8") as f: json.dump(qp_parsed,  f, indent=2)
    with open(ak_parsed_path,  "w", encoding="utf-8") as f: json.dump(ak_parsed,  f, indent=2)
    with open(ans_parsed_path, "w", encoding="utf-8") as f: json.dump(ans_parsed, f, indent=2)

    grading_ready_path = os.path.join(output_dir, "grading_ready.json")
    merged = merge(qp_parsed_path, ak_parsed_path, ans_parsed_path, ans_path)
    with open(grading_ready_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)

    logger.info("Stage 2 complete")

    # ── Stage 3: Grading ──────────────────────────────────────────────────
    logger.info("Stage 3: Grading answers...")

    graded_path = os.path.join(output_dir, "graded_output.json")
    grade_all(grading_ready_path, graded_path)

    logger.info("Stage 3 complete")

    # ── Stage 4: Feedback ─────────────────────────────────────────────────
    logger.info("Stage 4: Generating feedback...")

    final_path = os.path.join(output_dir, "final_output.json")
    result = generate_all_feedback(graded_path, final_path)

    logger.info("Stage 4 complete")
    logger.info("Pipeline complete: %s / %s", result['total_scored'], result['total_marks'])

    return result
