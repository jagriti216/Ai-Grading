"""
Combines DeBERTa, SBERT, Concept scores into final mark.
When concept_score=0 (no concepts matched), DeBERTa weight is reduced
to prevent false confidence from topic similarity alone.
"""

from stage3_grading.negation_checker import get_contradiction_penalty


def compute_text_score(
    deberta_score:    float,
    sbert_score:      float,
    concept_score:    float,
    matched_concepts: int,
    total_concepts:   int,
    max_marks:        int,
    expected_answer:  str = "",
    student_answer:   str = "",
) -> dict:

    # Dynamic weights based on concept coverage
    if total_concepts > 0 and matched_concepts == 0:
        # No concepts matched — trust DeBERTa less, concept absence is strong signal
        w_deberta = 0.50
        w_sbert   = 0.05
        w_concept = 0.45
    else:
        # Normal weights
        w_deberta = 0.65
        w_sbert   = 0.10
        w_concept = 0.25

    raw = w_deberta * deberta_score + w_sbert * sbert_score + w_concept * concept_score
    raw = max(0.0, min(1.0, raw))

    # Completeness cap: if the student covered less than half of the
    # expected concepts, don't let DeBERTa/SBERT's topic-overlap signal
    # push the score above a "mostly incomplete" ceiling.
    completeness_capped = False
    if total_concepts > 0 and (matched_concepts / total_concepts) < 0.5:
        cap = 0.4
        if raw > cap:
            raw = cap
            completeness_capped = True

    if expected_answer and student_answer:
        penalty, contradiction_debug = get_contradiction_penalty(expected_answer, student_answer)
    else:
        penalty = 1.0
        contradiction_debug = {"skipped": "not provided"}

    penalised_raw = raw * penalty
    score         = round(penalised_raw * max_marks, 1)

    return {
        "score":            score,
        "max_marks":        max_marks,
        "raw":              round(raw, 4),
        "penalised_raw":    round(penalised_raw, 4),
        "deberta_score":    round(deberta_score, 4),
        "sbert_score":      round(sbert_score, 4),
        "concept_score":    round(concept_score, 4),
        "matched_concepts": matched_concepts,
        "total_concepts":   total_concepts,
        "contradiction":    contradiction_debug,
        "completeness_capped": completeness_capped,
        "method":           "text",
    }


def compute_math_score(math_result: dict) -> dict:
    return {
        "score":       math_result["score"],
        "max_marks":   math_result["max_marks"],
        "raw":         round(math_result["score"] / math_result["max_marks"], 4) if math_result["max_marks"] else 0,
        "line_scores": math_result["line_scores"],
        "method":      "math",
    }
