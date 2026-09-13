"""
Tests for the fast regex layer (Layer 1) of stage3_grading/negation_checker.py.

Only cases that resolve via the relational-antonym regex are covered
here, so this suite stays fast and doesn't need to download the NLI
model (cross-encoder/nli-deberta-v3-small) in CI. The NLI layer (Layer 2)
is exercised manually / in integration testing instead.

Also covers the two "should NOT trigger" regression cases from
CHANGES.md's own test-case list, which the overfitting warning there
flags as a real risk of the hardcoded rules.
"""
from stage3_grading.negation_checker import get_contradiction_penalty, check_concept_contradiction


def test_relational_contradiction_oxygen_direction():
    penalty, debug = get_contradiction_penalty(
        "Plants release oxygen during photosynthesis.",
        "Plants absorb oxygen during photosynthesis.",
    )
    assert penalty == 0.15
    assert debug["contradicted"] is True
    assert debug["source"] == "relational"


def test_relational_contradiction_chamber_count():
    penalty, debug = get_contradiction_penalty(
        "The human heart is a four-chambered organ.",
        "The human heart is a two-chambered organ.",
    )
    assert penalty == 0.15


def test_no_negation_words_skips_check_entirely():
    # No negation words, no relational rule match — should short-circuit
    # to "not contradicted" without loading the NLI model at all.
    penalty, debug = get_contradiction_penalty(
        "Photosynthesis produces glucose from CO2 and water.",
        "Plants convert carbon dioxide and water into sugar.",
    )
    assert penalty == 1.0
    assert debug["nli_skipped"] == "no negation words"


def test_empty_student_answer_is_never_penalized_here():
    penalty, debug = get_contradiction_penalty("V = IR", "")
    assert penalty == 1.0
    assert debug == {"skipped": "empty"}


def test_check_concept_contradiction_catches_relational_mismatch():
    assert check_concept_contradiction(
        "releases oxygen", "the plant absorbs oxygen from the air"
    ) is True


def test_carbon_oxygen_rule_does_not_misfire_on_legitimate_blood_oxygen_answer():
    # Straight from CHANGES.md's own "test cases to validate after
    # changes" list — a legitimate blood-oxygen-transport answer must
    # not be misflagged by the carbon/oxygen relational rule just
    # because it's a plausible false-positive shape for that rule.
    penalty, debug = get_contradiction_penalty(
        "Red blood cells carry oxygen to tissues",
        "Blood transports oxygen throughout the body",
    )
    assert penalty == 1.0
