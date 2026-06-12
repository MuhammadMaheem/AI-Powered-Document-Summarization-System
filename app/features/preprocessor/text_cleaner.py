"""
Text cleaning utilities.

Produces a lowercased, noise-stripped version of the input text.
The *original* text is preserved separately so the final summary
can return sentences in their original casing.
"""

import re
from nltk.corpus import stopwords
from app.core.nlp.model_loader import ensure_nltk_resources

ensure_nltk_resources()

_STOP_WORDS = set(stopwords.words("english"))
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALPHA_RE = re.compile(r"[^a-z0-9\s]")


def clean_text(text: str) -> str:
    text = _URL_RE.sub(" ", text)
    text = text.lower()
    text = _NON_ALPHA_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def remove_stopwords(tokens: list) -> list:
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]
