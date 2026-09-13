"""
Contradiction detector — two layers:
Layer 1: Relational antonym regex (fast, no model)
Layer 2: NLI model (only when negation words present)
"""

import re
from transformers import pipeline

_nli_pipeline = None
NLI_MODEL             = "cross-encoder/nli-deberta-v3-small"
CONTRADICTION_PENALTY = 0.15
CONTRADICTION_THRESHOLD = 0.55

_RELATIONAL_ANTONYMS = [
    # oxygen direction
    (r'\breleases?\s+oxygen\b',                             r'\btakes?\s+(in\s+)?oxygen\b|\babsorbs?\s+oxygen\b'),
    (r'\btakes?\s+(in\s+)?oxygen\b|\babsorbs?\s+oxygen\b',  r'\breleases?\s+oxygen\b'),
    (r'\babsorbs?\s+CO2\b|\btakes?\s+(in\s+)?CO2\b',        r'\breleases?\s+CO2\b'),
    # equality vs proportion
    (r'\bequal\b|\bsame\b|\bidentical\b',                   r'\bdouble\b|\btwice\b|\bhalf\b|\btriple\b'),
    (r'\bdouble\b|\btwice\b',                               r'\bequal\b|\bsame\b|\bhalf\b'),
    # direction
    (r'\bhigh(?:er)?\s+to\s+low(?:er)?\b',                 r'\blow(?:er)?\s+to\s+high(?:er)?\b'),
    (r'\blow(?:er)?\s+to\s+high(?:er)?\b',                 r'\bhigh(?:er)?\s+to\s+low(?:er)?\b'),
    # increases / decreases
    (r'\bincreases?\b|\brises?\b',                          r'\bdecreases?\b|\bfalls?\b|\breduces?\b'),
    (r'\bdecreases?\b|\bfalls?\b|\breduces?\b',             r'\bincreases?\b|\brises?\b'),
    # requires / does not require
    (r'\bdoes\s+not\s+require|without\b|\bindependent\b',   r'\brequires?\b|\bneeds?\b|\bdepends?\s+on\b'),
    (r'\brequires?\b|\bneeds?\b|\bdepends?\s+on\b',         r'\bdoes\s+not\s+require|without\b|\bindependent\b'),
    # aerobic/anaerobic swap
    (r'\baerobic\b.*\bwithout\s+oxygen\b',                  r'\baerobic\b.*\bneeds?\s+oxygen\b|\baerobic\b.*\bwith\s+oxygen\b'),
    (r'\banaerobic\b.*\bwithout\s+oxygen\b',                r'\banaerobic\b.*\bneeds?\s+oxygen\b'),
    # carbon vs oxygen confusion
    (r'\bcarbon\b',                                         r'\boxygen\b(?!.*carbon)'),
    # four vs two chambers
    (r'\bfour[\s\-]chamber',                                r'\btwo[\s\-]?chamber|\b2\s*chamber'),
    (r'\btwo[\s\-]?chamber|\b2\s*chamber',                  r'\bfour[\s\-]chamber'),
    # voltage is NOT power/energy
    (r'\bvoltage\b.*\bpotential\s+difference\b',            r'\bvoltage\b.*\bpower\b|\bvoltage\b.*\benergy\b'),
    (r'\bvoltage\b.*\bpower\b|\bvoltage\b.*\benergy\b',     r'\bvoltage\b.*\bpotential\s+difference\b'),
    # order errors — pollination before seed
    (r'\bpollination\b.*\bfertili',                         r'\bseed\b.*\bpollination\b|\bfirst\b.*\bseed\b.*\bthen\b.*\bpollinat'),
    (r'\bseed\b.*\bpollinat',                               r'\bpollinat\b.*\bseed\b'),
    # before / after
    (r'\bfirst\b.*\bthen\b',                                r'\bthen\b.*\bfirst\b'),
    # destroys / preserves
    (r'\bdestroyed?\b|\bdenatured?\b',                      r'\bpreserved?\b|\bunchanged?\b'),
    (r'\bpreserved?\b|\bunchanged?\b',                      r'\bdestroyed?\b|\bdenatured?\b'),
]

_NEGATION_WORDS = re.compile(
    r"\b(not|no|never|neither|nor|cannot|can't|won't|isn't|aren't|doesn't|don't|"
    r"didn't|wasn't|weren't|without|absence|lack|fails|prevent|inhibit|stop)\b",
    re.IGNORECASE,
)


def _load_nli():
    global _nli_pipeline
    if _nli_pipeline is None:
        print(f"Loading NLI model ({NLI_MODEL})...")
        _nli_pipeline = pipeline(
            "text-classification",
            model=NLI_MODEL,
            return_all_scores=True,
            device=-1,
        )
        print("NLI model loaded.")
    return _nli_pipeline


def _has_negation(text: str) -> bool:
    return bool(_NEGATION_WORDS.search(text))


def _run_nli(nli, premise: str, hypothesis: str) -> dict:
    raw   = nli(f"{premise} [SEP] {hypothesis}")
    items = raw[0] if isinstance(raw[0], list) else raw
    return {item["label"].lower(): item["score"] for item in items}


def _check_relational(expected: str, student: str) -> tuple:
    for pat_a, pat_b in _RELATIONAL_ANTONYMS:
        exp_a = bool(re.search(pat_a, expected, re.IGNORECASE | re.DOTALL))
        stu_b = bool(re.search(pat_b, student,  re.IGNORECASE | re.DOTALL))
        exp_b = bool(re.search(pat_b, expected, re.IGNORECASE | re.DOTALL))
        stu_a = bool(re.search(pat_a, student,  re.IGNORECASE | re.DOTALL))
        if exp_a and stu_b:
            return True, f"relational: expected '{pat_a}' but student said '{pat_b}'"
        if exp_b and stu_a:
            return True, f"relational: expected '{pat_b}' but student said '{pat_a}'"
    return False, ""


def get_contradiction_penalty(expected_answer: str, student_answer: str) -> tuple:
    if not student_answer or not student_answer.strip():
        return 1.0, {"skipped": "empty"}

    debug = {}

    rel_contra, rel_rule = _check_relational(expected_answer, student_answer)
    debug["relational_contradiction"] = rel_contra
    if rel_contra:
        debug["relational_rule"] = rel_rule
        debug["contradicted"]    = True
        debug["source"]          = "relational"
        debug["penalty_applied"] = CONTRADICTION_PENALTY
        return CONTRADICTION_PENALTY, debug

    if not _has_negation(expected_answer) and not _has_negation(student_answer):
        debug["nli_skipped"]     = "no negation words"
        debug["contradicted"]    = False
        debug["penalty_applied"] = 1.0
        return 1.0, debug

    nli     = _load_nli()
    fwd     = _run_nli(nli, expected_answer, student_answer)
    rev     = _run_nli(nli, student_answer,  expected_answer)
    max_c   = max(fwd.get("contradiction", 0.0), rev.get("contradiction", 0.0))
    contra  = max_c >= CONTRADICTION_THRESHOLD

    debug["max_contradiction"] = round(max_c, 4)
    debug["contradicted"]      = contra
    debug["source"]            = "nli" if contra else "none"
    debug["penalty_applied"]   = CONTRADICTION_PENALTY if contra else 1.0

    return (CONTRADICTION_PENALTY if contra else 1.0), debug


def check_concept_contradiction(concept: str, student_answer: str) -> bool:
    rel_contra, _ = _check_relational(concept, student_answer)
    if rel_contra:
        return True
    if not _has_negation(concept) and not _has_negation(student_answer):
        return False
    nli    = _load_nli()
    scores = _run_nli(nli, concept, student_answer)
    return scores.get("contradiction", 0.0) >= CONTRADICTION_THRESHOLD