"""
Weighted sentence ranker with positional bias.

Combines frequency and TF-IDF scores then applies a small positional
boost to sentences at the beginning and end of a document (where key
information tends to appear in real-world reports and articles).

Algorithm:
  combined_score = (freq_weight * freq_score) + (tfidf_weight * tfidf_score)
  positional_boost applied to indices 0, 1, and -1

The top-N sentences are selected by score, then returned in their
*original document order* so the summary reads naturally.
"""

from typing import List, Tuple

POSITIONAL_BOOST = 0.1


def rank_and_select(
    sentences: List[str],
    freq_scores: List[float],
    tfidf_scores: List[float],
    ratio: float = 0.3,
    freq_weight: float = 0.5,
    tfidf_weight: float = 0.5,
) -> Tuple[List[str], List[dict]]:
    if not sentences:
        return [], []

    n = len(sentences)
    combined = []

    for i in range(n):
        score = (freq_weight * freq_scores[i]) + (tfidf_weight * tfidf_scores[i])

        # Positional boost: first two sentences and last sentence matter most.
        if i in (0, 1) or i == n - 1:
            score = min(score + POSITIONAL_BOOST, 1.0)

        combined.append({"index": i, "sentence": sentences[i], "score": round(score, 4)})

    num_sentences = max(1, round(ratio * n))

    ranked = sorted(combined, key=lambda x: x["score"], reverse=True)
    top = sorted(ranked[:num_sentences], key=lambda x: x["index"])

    summary_sentences = [item["sentence"] for item in top]
    return summary_sentences, combined
