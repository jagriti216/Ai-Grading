"""
Tests for stage3_grading/math_scorer.py — numeric tolerance matching
and SymPy-based symbolic formula equivalence.
"""
from stage3_grading.math_scorer import (
    check_numerical_match,
    check_formula_match,
    score_math_answer,
)


def test_numerical_match_within_tolerance():
    assert check_numerical_match("V = 40V", "The voltage is about 41V") is True


def test_numerical_match_outside_tolerance():
    assert check_numerical_match("V = 40V", "The voltage is 22V") is False


def test_formula_match_recognizes_symbolic_equivalence():
    # 20*2 = 40 written differently should still be recognized as equal to IR
    assert check_formula_match("V = I*R", "V = R*I") is True


def test_formula_match_rejects_wrong_formula():
    # CHANGES.md Q2: student wrote I = V + R instead of V = IR
    assert check_formula_match("V = I*R", "V = I + R") is False


def test_score_math_answer_awards_full_credit_line_by_line():
    expected = "F = ma\nF = 10×2 = 20N"
    student = "F = ma\nF = 10×2 = 20N"
    result = score_math_answer(expected, student, max_marks=4)
    assert result["score"] == 4.0
    assert all(line["awarded"] for line in result["line_scores"])


def test_score_math_answer_zero_for_empty_student_answer():
    result = score_math_answer("F = ma", "", max_marks=4)
    assert result["score"] == 0.0
