"""
Keyword extraction.

Uses two complementary strategies and merges their results:

1. TF-IDF top terms — statistically important words that are common
   within sentences but rare across the document corpus.

2. spaCy noun chunks — noun phrases extracted by the POS tagger,
   which tend to be semantically meaningful regardless of raw frequency.
"""

from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from app.core.nlp.model_loader import get_spacy_nlp


def extract_keywords(sentences: List[str], token_lists: List[List[str]], top_n: int = 10) -> List[str]:
    tfidf_keywords = _tfidf_keywords(token_lists, top_n)
    spacy_keywords = _spacy_noun_chunks(sentences, top_n // 2)

    # Merge: spaCy results first (they tend to be more readable), then TF-IDF.
    seen = set()
    combined = []
    for kw in spacy_keywords + tfidf_keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            combined.append(kw)

    return combined[:top_n]


def _tfidf_keywords(token_lists: List[List[str]], top_n: int) -> List[str]:
    cleaned = [" ".join(tokens) for tokens in token_lists if tokens]
    if not cleaned:
        return []

    try:
        vectorizer = TfidfVectorizer(max_features=top_n * 2)
        vectorizer.fit_transform(cleaned)
        feature_names = vectorizer.get_feature_names_out()
        return list(feature_names[:top_n])
    except ValueError:
        return []


def _spacy_noun_chunks(sentences: List[str], top_n: int) -> List[str]:
    if not sentences:
        return []

    nlp = get_spacy_nlp()
    chunks = []
    sample = " ".join(sentences[:20])  # limit to keep processing fast
    doc = nlp(sample)

    for chunk in doc.noun_chunks:
        text = chunk.text.strip().lower()
        if 2 <= len(text.split()) <= 4:
            chunks.append(chunk.text.strip())

    # Deduplicate while preserving order.
    seen = set()
    unique = []
    for c in chunks:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique.append(c)

    return unique[:top_n]
