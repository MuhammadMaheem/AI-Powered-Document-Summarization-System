"""
Sentence importance scoring for the analytics panel.

Returns structured data for each sentence: its text, combined importance
score, and a label (high / medium / low) used in the UI.
"""

from typing import List


def build_sentence_scores(
    sentences: List[str],
    combined_scores: List[dict],
) -> List[dict]:
    if not sentences or not combined_scores:
        return []

    result = []
    for item in combined_scores:
        score = item["score"]
        if score >= 0.65:
            label = "high"
        elif score >= 0.35:
            label = "medium"
        else:
            label = "low"

        result.append({
            "sentence": item["sentence"],
            "score": score,
            "label": label,
        })

    return result
