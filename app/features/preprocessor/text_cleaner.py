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

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALPHA_RE = re.compile(r"[^a-z0-9\s]")

_stopword_cache: dict = {}


def _get_stopwords(language: str = "english") -> set:
    if language not in _stopword_cache:
        try:
            _stopword_cache[language] = set(stopwords.words(language))
        except OSError:
            _stopword_cache[language] = set(stopwords.words("english"))
    return _stopword_cache[language]


def clean_text(text: str) -> str:
    text = _URL_RE.sub(" ", text)
    text = text.lower()
    text = _NON_ALPHA_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def remove_stopwords(tokens: list, language: str = "english") -> list:
    stop = _get_stopwords(language)
    return [t for t in tokens if t not in stop and len(t) > 1]
