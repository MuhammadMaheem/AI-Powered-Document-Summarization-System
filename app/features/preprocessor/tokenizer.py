"""
Tokenization utilities wrapping NLTK Punkt sentence tokeniser
and word tokeniser.
"""

import nltk
from app.core.nlp.model_loader import ensure_nltk_resources

ensure_nltk_resources()


def sentence_tokenize(text: str) -> list:
    sentences = nltk.sent_tokenize(text)
    return [s.strip() for s in sentences if s.strip()]


def word_tokenize(text: str) -> list:
    return nltk.word_tokenize(text.lower())


def filter_tokens(tokens: list) -> list:
    return [t for t in tokens if t.isalpha() and len(t) > 1]
