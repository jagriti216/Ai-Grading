"""
Main grading orchestrator.
Reads grading_ready.json, scores each question, saves graded_output.json.
"""

import os
import json
from stage3_grading.detector       import is_math_question, split_into_lines
from stage3_grading.deberta_scorer import get_deberta_score
from stage3_grading.sbert_scorer   import get_sbert_score
from stage3_grading.math_scorer    import score_math_answer
from stage3_grading.normalizer     import compute_text_score, compute_math_score
from stage3_grading.concept_scorer import ConceptScorer

_concept_scorer = None


def get_concept_scorer():
    global _concept_scorer
    if _concept_scorer is None:
        _concept_scorer = ConceptScorer()
    return _concept_scorer


def grade_question(question: dict) -> dict:
    q_text   = question["question_text"]
    expected = question["expected_answer"]
    student  = question["student_answer"]
    max_mks  = question["max_marks"]

    # empty answer → 0 immediately
    if not student or not student.strip():
        question["score"]     = 0.0
        question["breakdown"] = {"method": "empty", "raw": 0.0}
        return question

    # no expected answer → skip
    if not expected or not expected.strip():
        question["score"]     = 0.0
        question["breakdown"] = {"method": "no_key", "raw": 0.0}
        return question

    # detect question type
    math = is_math_question(q_text, expected, student)

    if math:
        # per-line math/formula scoring
        math_result = score_math_answer(expected, student, max_mks)
        result      = compute_math_score(math_result)
    else:
        # DeBERTa + SBERT + Concept coverage holistic scoring
        deberta = get_deberta_score(q_text, expected, student)
        sbert   = get_sbert_score(expected, student)
        concept_scorer = get_concept_scorer()
        concept_res = concept_scorer.score(expected, student)
        result  = compute_text_score(
            deberta_score    = deberta,
            sbert_score      = sbert,
            concept_score    = concept_res["coverage"],
            matched_concepts = concept_res["matched_concepts"],
            total_concepts   = concept_res["total_concepts"],
            max_marks        = max_mks,
            # NEW: pass raw answers so the NLI contradiction gate can run
            expected_answer  = expected,
            student_answer   = student,
        )

    question["score"]     = result["score"]
    question["breakdown"] = result

    return question


def grade_all(grading_ready_path: str, output_path: str) -> dict:
    with open(grading_ready_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Student   : {data['student_name']}")
    print(f"Questions : {data['num_questions']}")
    print(f"Total marks: {data['total_marks']}")
    print()

    total_scored = 0

    for i, question in enumerate(data["questions"]):
        qnum   = question["q_number"]
        method = "math" if is_math_question(
            question["question_text"],
            question["expected_answer"],
            question["student_answer"]
        ) else "text"

        print(f"  Grading {qnum} [{question['max_marks']} marks] [{method}]...", end=" ")

        try:
            question             = grade_question(question)
            data["questions"][i] = question
            scored               = question["score"] or 0
            total_scored        += scored
            print(f"{question['score']} / {question['max_marks']}")
        except Exception as e:
            print(f"FAILED — {e}")
            question["score"]     = None
            question["breakdown"] = {"error": str(e)}

    data["total_scored"] = round(total_scored, 1)
    data["percentage"]   = round((total_scored / data["total_marks"]) * 100, 1) if data["total_marks"] else 0

    print()
    print(f"Total: {data['total_scored']} / {data['total_marks']} ({data['percentage']}%)")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved to {output_path}")
    return data


if __name__ == "__main__":
    grade_all(
        grading_ready_path = os.path.join("outputs", "grading_ready.json"),
        output_path        = os.path.join("outputs", "graded_output.json")
    )
