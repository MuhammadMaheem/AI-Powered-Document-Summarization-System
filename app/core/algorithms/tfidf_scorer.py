"""
TF-IDF based sentence scorer.

Each sentence is treated as a mini-document.  sklearn's TfidfVectorizer
builds a term-document matrix and we score each sentence by summing the
TF-IDF weights of all its terms.

Why TF-IDF beats raw frequency:
  - TF (term frequency) rewards words that are common *in a sentence*.
  - IDF (inverse document frequency) penalises words that appear in
    every sentence (they carry little discriminating information).
  - Together they highlight sentences that contain rare-but-important terms.
"""

from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


def score_sentences(sentences: List[str], token_lists: List[List[str]]) -> List[float]:
    if not sentences or not token_lists:
        return []

    # Reconstruct cleaned sentence strings from token lists for the vectoriser.
    cleaned_sentences = [" ".join(tokens) for tokens in token_lists]

    # Filter out empty strings; keep track of their original indices.
    non_empty = [(i, s) for i, s in enumerate(cleaned_sentences) if s.strip()]
    if not non_empty:
        return [0.0] * len(sentences)

    indices, texts = zip(*non_empty)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)

    # Row-wise sum gives the total TF-IDF weight for each sentence.
    raw_scores_sparse = np.array(tfidf_matrix.sum(axis=1)).flatten()

    scores = [0.0] * len(sentences)
    for rank, idx in enumerate(indices):
        scores[idx] = float(raw_scores_sparse[rank])

    max_score = max(scores) if max(scores) > 0 else 1.0
    return [s / max_score for s in scores]
