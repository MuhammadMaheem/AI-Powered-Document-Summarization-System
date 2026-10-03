"""
Word frequency analysis.

Returns the top-N most frequent words from the flat token list.
"""

from collections import Counter
from typing import List


def top_word_frequencies(flat_tokens: List[str], top_n: int = 15) -> List[dict]:
    if not flat_tokens:
        return []

    counts = Counter(flat_tokens)
    return [
        {"word": word, "count": count}
        for word, count in counts.most_common(top_n)
    ]
