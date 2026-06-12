"""
Frequency-based sentence scorer.

Each sentence receives a score equal to the sum of its words'
normalised document-wide frequencies.  Words that appear often in
the document are considered important; sentences rich in those words
score higher.

Steps:
  1. Count raw word occurrences across all cleaned token lists.
  2. Normalise: divide every count by the maximum count → range [0, 1].
  3. Score each sentence by summing the normalised frequencies of its tokens.
  4. Normalise sentence scores to [0, 1] so they are comparable with other
     scorers.
"""

from collections import Counter
from typing import List


def score_sentences(sentences: List[str], token_lists: List[List[str]]) -> List[float]:
    if not sentences or not token_lists:
        return []

    all_tokens = [t for tokens in token_lists for t in tokens]
    if not all_tokens:
        return [0.0] * len(sentences)

    raw_freq = Counter(all_tokens)
    max_freq = max(raw_freq.values())
    norm_freq = {word: count / max_freq for word, count in raw_freq.items()}

    raw_scores = [
        sum(norm_freq.get(token, 0.0) for token in tokens)
        for tokens in token_lists
    ]

    max_score = max(raw_scores) if max(raw_scores) > 0 else 1.0
    return [s / max_score for s in raw_scores]
