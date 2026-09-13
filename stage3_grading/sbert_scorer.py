"""
SBERT textual similarity scorer.
Uses sentence-transformers/all-MiniLM-L6-v2 locally.
Downloads once, cached after first run.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

_model = None


def load_model():
    global _model
    if _model is None:
        print("Loading SBERT model...")
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("SBERT loaded successfully")
    return _model


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def get_sbert_score(expected_answer: str, student_answer: str) -> float:
    """
    Returns cosine similarity between expected and student answer embeddings.
    0 = completely different, 1 = identical meaning.
    """
    if not student_answer or not student_answer.strip():
        return 0.0

    model = load_model()

    embeddings = model.encode([expected_answer, student_answer])
    score      = cosine_similarity(embeddings[0], embeddings[1])

    return round(max(0.0, score), 4)


if __name__ == "__main__":
    tests = [
        (
            "Photosynthesis converts CO2 and water into glucose using sunlight.",
            "Plants use sunlight and carbon dioxide to make food."
        ),
        (
            "Photosynthesis converts CO2 and water into glucose using sunlight.",
            "Plants drink water at night to grow."
        ),
        (
            "V = IR. Voltage equals current times resistance.",
            "Ohm's law is I = V + R."
        ),
    ]

    for expected, student in tests:
        score = get_sbert_score(expected, student)
        print(f"SBERT: {score:.4f} | Student: {student[:50]}")
