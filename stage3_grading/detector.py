"""
Detects whether a question requires math or text scoring.
Math mode triggers when question asks for calculation AND answer has numbers.
Also catches pure formula definition questions like "What is Ohm's Law? V=IR"
"""

import re

_NUMERIC_PATTERNS = [
    r'\d+\s*[×\*\/]\s*\d+',
    r'\d+\s*(W|V|A|N|J|kg|m|s|Hz)\b',
    r'=\s*\d+\.?\d*\s*(W|V|A|N|J|N)',
    r'[A-Za-z]\s*=\s*[A-Za-z0-9]+\s*[×\*]\s*[A-Za-z0-9]+',
]

_CALC_KEYWORDS = re.compile(
    r'\b(calculate|compute|find|determine|evaluate|solve|what is the value|how much|how many)\b',
    re.IGNORECASE
)

_FORMULA_PATTERN = re.compile(
    r'[A-Za-z]\s*=\s*[A-Za-z]+\s*[\+\-\*\/×]?\s*[A-Za-z]',
    re.IGNORECASE
)


def has_formula(text: str) -> bool:
    return bool(_FORMULA_PATTERN.search(text))


def is_math_question(question_text: str, expected_answer: str, student_answer: str = "") -> bool:
    # calculation keyword in question + numeric computation in answer
    if _CALC_KEYWORDS.search(question_text):
        for pattern in _NUMERIC_PATTERNS:
            if re.search(pattern, expected_answer, re.IGNORECASE):
                return True
        if re.search(r'[A-Za-z]\s*=\s*[A-Za-z0-9\s×\*]+\s*=\s*\d+', expected_answer):
            return True

    # formula-definition questions (e.g. "What is Ohm's Law?") don't use a
    # calculation keyword but still need symbolic/formula comparison rather
    # than free-text scoring — route to math mode when both the expected
    # and student answers state a formula.
    if has_formula(expected_answer) and student_answer and has_formula(student_answer):
        return True

    return False


def split_into_lines(expected_answer: str) -> list:
    lines = expected_answer.split("\n")
    if len(lines) == 1:
        lines = re.split(r'\.\s+', expected_answer)
    cleaned = []
    for l in lines:
        l = re.sub(r'^\s*[\d\-\•\*\.]+\s*', '', l).strip()
        if len(l) >= 8 and re.search(r'[A-Za-z0-9]', l):
            cleaned.append(l)
    return cleaned


if __name__ == "__main__":
    tests = [
        ("What is photosynthesis?",        "Plants convert CO2 and water into glucose."),
        ("What is Ohm's Law?",             "Ohm's Law states V = IR. Current proportional to voltage."),
        ("Calculate voltage and power.",   "V = IR = 20×2 = 40V. P = VI = 40×2 = 80W."),
        ("Find the force if m=10, a=2.",   "F = ma = 10×2 = 20N"),
        ("Explain Newton's second law.",   "F = ma. Force equals mass times acceleration."),
    ]
    for q, a in tests:
        result = is_math_question(q, a)
        print(f"{'MATH' if result else 'TEXT'} | {q}")
