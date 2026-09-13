"""
Concept coverage scorer.
Extracts key concepts from expected answer and checks if student covered them.

Concept boundaries are found by splitting on '.', ';', '\\n' AND commas /
coordinating conjunctions ("and", "or") — the comma/conjunction split is
what actually fixes the old bug where a comma-separated list of facts
("pollination, fertilization, and seed formation") collapsed into one
concept and evaded coverage checking (CHANGES.md's Q14 case). Each clause
stays a complete, grammatical fragment, which is what makes it embed
meaningfully for the similarity match below.

KeyBERT was tried first as the primary extraction method and rejected:
tested against real cases, it extracts contiguous n-gram substrings of
the answer key's own wording rather than complete clauses, which made
concept-matching *less* reliable, not more — a fully correct, fluently
rephrased student answer scored lower coverage than a wrong, scrambled
one, because the extracted "concepts" were often grammatically broken
fragments. KeyBERT is kept only as a secondary pass, for the case a
clause-split still leaves one long run-on segment (>15 words) with no
further delimiter to split on.
"""

import re
from sentence_transformers import SentenceTransformer, util
from stage3_grading.negation_checker import check_concept_contradiction

CONCEPT_MATCH_THRESHOLD = 0.68   # raised from 0.65 to reduce false positives
MAX_CONCEPTS = 6
LONG_CLAUSE_WORD_COUNT = 15       # above this, try KeyBERT to sub-split a run-on clause

_shared_embedder = None
_keybert_model = None


def _get_shared_embedder() -> SentenceTransformer:
    global _shared_embedder
    if _shared_embedder is None:
        _shared_embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _shared_embedder


def _get_keybert():
    global _keybert_model
    if _keybert_model is None:
        from keybert import KeyBERT
        _keybert_model = KeyBERT(model=_get_shared_embedder())
    return _keybert_model


def _split_into_clauses(expected_answer: str) -> list:
    # split on sentence boundaries, then further split each sentence on
    # commas and coordinating conjunctions so multi-fact lists don't
    # collapse into a single concept
    sentences = re.split(r'[.;\n]', expected_answer)
    clauses = []
    for sentence in sentences:
        sub_parts = re.split(r',|\band\b|\bor\b', sentence, flags=re.IGNORECASE)
        clauses.extend(sub_parts)
    return clauses


def _sub_split_long_clause(clause: str) -> list:
    """KeyBERT as a secondary pass — only for a long, undelimited run-on clause."""
    try:
        pairs = _get_keybert().extract_keywords(
            clause,
            keyphrase_ngram_range=(3, 6),
            stop_words=None,
            use_mmr=True,
            diversity=0.6,
            top_n=3,
        )
        phrases = [phrase for phrase, score in pairs if score >= 0.3]
        if phrases:
            return phrases
    except Exception:
        pass
    return [clause]


def extract_concepts_from_text(expected_answer: str) -> list:
    if not expected_answer or not expected_answer.strip():
        return []

    concepts = []
    seen = set()

    for clause in _split_into_clauses(expected_answer):
        cleaned = clause.strip()
        if len(cleaned) <= 5:
            continue

        candidates = [cleaned] if len(cleaned.split()) <= LONG_CLAUSE_WORD_COUNT else _sub_split_long_clause(cleaned)

        for candidate in candidates:
            norm = candidate.lower().strip()
            if norm and norm not in seen:
                seen.add(norm)
                concepts.append(candidate.strip())

    return concepts[:MAX_CONCEPTS]


class ConceptScorer:
    def __init__(self):
        self.model = _get_shared_embedder()

    def extract_concepts(self, expected_answer):
        return extract_concepts_from_text(expected_answer)

    def score(self, expected_answer, student_answer):
        concepts = self.extract_concepts(expected_answer)

        if not concepts:
            return {"coverage": 0.0, "matched_concepts": 0, "total_concepts": 0}

        student_emb = self.model.encode(student_answer, convert_to_tensor=True)
        matched = 0

        for concept in concepts:
            concept_emb = self.model.encode(concept, convert_to_tensor=True)
            sim = util.cos_sim(concept_emb, student_emb).item()

            if sim >= CONCEPT_MATCH_THRESHOLD:
                if check_concept_contradiction(concept, student_answer):
                    continue
                matched += 1

        return {
            "coverage":        matched / len(concepts),
            "matched_concepts": matched,
            "total_concepts":  len(concepts)
        }
