"""
Tests for stage3_grading/normalizer.py — ensemble weighting, the
completeness cap (CHANGES.md Q10 fix), and math score passthrough.

expected_answer/student_answer are left blank in these calls so the
contradiction check short-circuits ("not provided") instead of loading
the NLI model — keeping this suite fast and network-free.
"""
from stage3_grading.normalizer import compute_text_score, compute_math_score


def test_normal_weighting_when_concepts_matched():
    result = compute_text_score(
        deberta_score=0.8, sbert_score=0.7, concept_score=1.0,
        matched_concepts=2, total_concepts=2, max_marks=4,
    )
    # 0.65*0.8 + 0.10*0.7 + 0.25*1.0 = 0.84
    assert result["raw"] == 0.84
    assert result["completeness_capped"] is False


def test_reweights_toward_concept_when_zero_matched():
    # 0/3 matched also means the completeness ratio is 0 < 0.5, so the
    # completeness cap (0.4) kicks in on top of the reweighting — even
    # though the reweighted raw score (0.50*0.9 + 0.05*0.8 + 0.45*0.0 =
    # 0.49) would otherwise have let a zero-concept answer score close
    # to half marks purely off DeBERTa/SBERT topic familiarity.
    result = compute_text_score(
        deberta_score=0.9, sbert_score=0.8, concept_score=0.0,
        matched_concepts=0, total_concepts=3, max_marks=4,
    )
    assert result["raw"] == 0.4
    assert result["completeness_capped"] is True


def test_completeness_cap_limits_incomplete_answers():
    # CHANGES.md Q10: DeBERTa/SBERT both high despite missing half the
    # expected concepts (student covered the stomach but not the
    # intestine) — raw score should be capped at 0.4 instead of ~0.75.
    result = compute_text_score(
        deberta_score=0.70, sbert_score=0.80, concept_score=0.5,
        matched_concepts=1, total_concepts=3, max_marks=4,
    )
    assert result["completeness_capped"] is True
    assert result["raw"] == 0.4
    assert result["score"] == 1.6


def test_completeness_cap_not_applied_when_majority_matched():
    result = compute_text_score(
        deberta_score=0.9, sbert_score=0.9, concept_score=0.75,
        matched_concepts=3, total_concepts=4, max_marks=4,
    )
    assert result["completeness_capped"] is False


def test_compute_math_score_passthrough():
    math_result = {"score": 3.0, "max_marks": 4, "line_scores": []}
    result = compute_math_score(math_result)
    assert result["method"] == "math"
    assert result["raw"] == 0.75
