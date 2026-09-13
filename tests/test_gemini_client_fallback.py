"""
Tests for the regex-based local fallback parsing in
stage2_parser/gemini_client.py — the safety net used when Gemini is
unavailable or the circuit breaker has tripped.
"""
from stage2_parser.gemini_client import split_blocks_by_question, parse_marks_from_text


def test_split_blocks_by_question_basic():
    text = "1) What is gravity?\nIt pulls things down.\n2) What is inertia?\nObjects resist change."
    blocks = split_blocks_by_question(text)
    assert [b[0] for b in blocks] == [1, 2]
    assert "gravity" in blocks[0][1]
    assert "inertia" in blocks[1][1]


def test_split_blocks_by_question_no_matches_returns_empty():
    assert split_blocks_by_question("no question numbering here at all") == []


def test_parse_marks_sums_split_marks():
    assert parse_marks_from_text("Explain the process (3+3 Marks)") == 6


def test_parse_marks_single_bracketed():
    assert parse_marks_from_text("What is photosynthesis? (5 marks)") == 5


def test_parse_marks_bare_number():
    assert parse_marks_from_text("Define entropy. 4 marks") == 4


def test_parse_marks_returns_none_when_absent():
    assert parse_marks_from_text("Define entropy.") is None
