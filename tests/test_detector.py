"""
Regression tests for stage3_grading/detector.py's math/text routing.

Includes the Q2 case documented in CHANGES.md: a formula-definition
question ("What is Ohm's Law?") with no calculation keyword was being
routed to the text scorer instead of the math scorer, letting a wrong
formula ("I = V + R") score 0.7/2 via DeBERTa's topical familiarity
with Ohm's Law instead of being caught as symbolically incorrect.
"""
from stage3_grading.detector import is_math_question


def test_calculate_keyword_with_numeric_answer_is_math():
    assert is_math_question(
        "Calculate the voltage and power.",
        "V = IR = 20×2 = 40V. P = VI = 40×2 = 80W.",
    ) is True


def test_plain_definition_question_is_text():
    assert is_math_question(
        "What is photosynthesis?",
        "Plants convert CO2 and water into glucose using sunlight.",
    ) is False


def test_formula_definition_question_routes_to_math_when_student_also_uses_formula():
    # CHANGES.md Q2: no "calculate" keyword, but both expected and student
    # answers state a formula — should now be treated as math, not text.
    assert is_math_question(
        "What is Ohm's Law?",
        "Ohm's Law states V = IR.",
        "I = V + R",
    ) is True


def test_formula_question_without_student_formula_stays_text():
    # If the student didn't write a formula at all, there's nothing for
    # the math/SymPy scorer to compare against — stay on the text path.
    assert is_math_question(
        "What is Ohm's Law?",
        "Ohm's Law states V = IR.",
        "It relates voltage, current and resistance.",
    ) is False
