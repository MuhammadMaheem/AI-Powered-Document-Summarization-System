"""
Sentence importance scoring for the analytics panel.

Returns structured data for each sentence: its text, combined importance
score, rank (1 = most important), and a label (high / medium / low).
Labels are rank-based (top third = high) so the distribution is always
meaningful regardless of absolute score values.
"""

from typing import List


def build_sentence_scores(
    sentences: List[str],
    combined_scores: List[dict],
) -> List[dict]:
    if not sentences or not combined_scores:
        return []

    n = len(combined_scores)
    sorted_idx = sorted(range(n), key=lambda i: -combined_scores[i]["score"])
    rank_map = {orig_i: rank for rank, orig_i in enumerate(sorted_idx)}

    result = []
    for i, item in enumerate(combined_scores):
        pct = rank_map[i] / max(1, n - 1)
        label = "high" if pct <= 0.33 else ("medium" if pct <= 0.66 else "low")
        result.append({
            "sentence": item["sentence"],
            "score": item["score"],
            "rank": rank_map[i] + 1,
            "label": label,
        })

    return result
