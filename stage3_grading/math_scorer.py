"""
Math/formula scorer for questions involving equations and numerical answers.
Uses SymPy for symbolic comparison and regex for numerical extraction.
"""

import re
import math
from typing import Optional


def extract_numbers(text: str) -> list:
    """Extracts all numbers from text."""
    return [float(x) for x in re.findall(r'-?\d+\.?\d*', text)]


def extract_formula(text: str) -> Optional[str]:
    """
    Extracts the formula/equation part from a line of text.
    Returns None if no formula found.
    """
    # match patterns like V = IR, F = ma, x = 40
    match = re.search(r'([A-Za-z]+)\s*=\s*(.+?)(?:\.|$)', text)
    if match:
        return match.group(0).strip()
    return None


def check_numerical_match(expected_line: str, student_answer: str, tolerance: float = 0.05) -> bool:
    """
    Checks if the numerical values in expected line appear in student answer.
    Uses relative tolerance of 5% for floating point comparison.
    """
    expected_nums = extract_numbers(expected_line)
    student_nums  = extract_numbers(student_answer)

    if not expected_nums:
        return False

    for exp_num in expected_nums:
        found = False
        for stu_num in student_nums:
            if exp_num == 0:
                if abs(stu_num) < 1e-6:
                    found = True
                    break
            else:
                if abs((stu_num - exp_num) / exp_num) <= tolerance:
                    found = True
                    break
        if not found:
            return False

    return True


def check_formula_match(expected_line: str, student_answer: str) -> bool:
    """
    Checks if student answer contains the correct formula.
    Uses SymPy for symbolic equivalence when possible.
    """
    try:
        from sympy import symbols, simplify
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

        transformations = standard_transformations + (implicit_multiplication_application,)

        # extract formula from expected
        exp_formula = extract_formula(expected_line)
        if not exp_formula or "=" not in exp_formula:
            return check_numerical_match(expected_line, student_answer)

        exp_lhs, exp_rhs = exp_formula.split("=", 1)

        # look for same LHS variable in student answer
        lhs_var = exp_lhs.strip()
        pattern = rf'{re.escape(lhs_var)}\s*=\s*(.+?)(?:\.|$|\n)'
        match   = re.search(pattern, student_answer, re.IGNORECASE)

        if not match:
            # formula not found in student answer
            return False

        stu_rhs = match.group(1).strip()

        # symbolic comparison
        exp_expr = parse_expr(exp_rhs.strip(),   transformations=transformations)
        stu_expr = parse_expr(stu_rhs.strip(),   transformations=transformations)

        return simplify(exp_expr - stu_expr) == 0

    except Exception:
        # fallback to numerical check if sympy fails
        return check_numerical_match(expected_line, student_answer)


def score_math_answer(expected_answer: str, student_answer: str, max_marks: int) -> dict:
    """
    Scores math answer by checking each line of expected answer against student answer.

    Returns:
    {
        "score": 2.0,
        "max_marks": 4,
        "line_scores": [
            {"line": "V = IR = 40V", "awarded": True,  "marks": 2.0},
            {"line": "P = VI = 80W", "awarded": False, "marks": 0.0}
        ]
    }
    """
    if not student_answer or not student_answer.strip():
        return {"score": 0.0, "max_marks": max_marks, "line_scores": []}

    # split expected answer into lines
    lines = [l.strip() for l in re.split(r'\n|\.(?=\s)', expected_answer) if l.strip()]

    if not lines:
        return {"score": 0.0, "max_marks": max_marks, "line_scores": []}

    marks_per_line = max_marks / len(lines)
    total_score    = 0.0
    line_scores    = []

    for line in lines:
        # determine if line has formula or just numbers
        has_formula = bool(re.search(r'[A-Za-z]\s*=\s*[A-Za-z0-9]', line))

        if has_formula:
            awarded = check_formula_match(line, student_answer)
        else:
            awarded = check_numerical_match(line, student_answer)

        marks = marks_per_line if awarded else 0.0
        total_score += marks

        line_scores.append({
            "line":    line,
            "awarded": awarded,
            "marks":   round(marks, 2)
        })

    return {
        "score":       round(total_score, 1),
        "max_marks":   max_marks,
        "line_scores": line_scores
    }


if __name__ == "__main__":
    tests = [
        {
            "expected": "V = IR = 20×2 = 40V\nP = VI = 40×2 = 80W",
            "student":  "Voltage = 20+2 = 22V. Power = 22×2 = 44W.",
            "marks":    4
        },
        {
            "expected": "V = IR = 20×2 = 40V\nP = VI = 40×2 = 80W",
            "student":  "V = IR = 20×2 = 40V. Power P = VI = 40×2 = 80W.",
            "marks":    4
        },
        {
            "expected": "F = ma\nF = 10×2 = 20N",
            "student":  "F = ma = 10×2 = 20N",
            "marks":    4
        }
    ]

    for t in tests:
        result = score_math_answer(t["expected"], t["student"], t["marks"])
        print(f"\nScore: {result['score']} / {result['max_marks']}")
        for ls in result["line_scores"]:
            status = "✓" if ls["awarded"] else "✗"
            print(f"  {status} [{ls['marks']}] {ls['line']}")
