"""
Singleton wrappers for NLTK and spaCy resources.

Both are loaded once at first use and reused across requests,
avoiding the overhead of repeated disk I/O.
"""

import threading
import nltk
import spacy

_lock = threading.Lock()
_spacy_nlp = None


def ensure_nltk_resources():
    required = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
        ("taggers/averaged_perceptron_tagger", "averaged_perceptron_tagger"),
    ]
    for path, name in required:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)


def get_spacy_nlp():
    global _spacy_nlp
    if _spacy_nlp is not None:
        return _spacy_nlp

    with _lock:
        if _spacy_nlp is None:
            try:
                _spacy_nlp = spacy.load("en_core_web_sm", disable=["ner"])
            except OSError:
                raise RuntimeError(
                    "spaCy model not found. Run: python -m spacy download en_core_web_sm"
                )
    return _spacy_nlp
