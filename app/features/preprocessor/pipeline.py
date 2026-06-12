"""
Preprocessing pipeline.

Chains together sentence segmentation, word tokenisation, stopword
removal, and token filtering into a single callable that returns a
structured result dict consumed by the summariser and analytics modules.
"""

from dataclasses import dataclass, field
from typing import List

from app.features.preprocessor.tokenizer import sentence_tokenize, word_tokenize, filter_tokens
from app.features.preprocessor.text_cleaner import remove_stopwords


@dataclass
class PreprocessResult:
    raw_sentences: List[str] = field(default_factory=list)
    token_lists: List[List[str]] = field(default_factory=list)
    flat_tokens: List[str] = field(default_factory=list)


def run(text: str) -> PreprocessResult:
    sentences = sentence_tokenize(text)
    token_lists = []
    flat_tokens = []

    for sentence in sentences:
        raw_tokens = word_tokenize(sentence)
        filtered = filter_tokens(raw_tokens)
        cleaned = remove_stopwords(filtered)
        token_lists.append(cleaned)
        flat_tokens.extend(cleaned)

    return PreprocessResult(
        raw_sentences=sentences,
        token_lists=token_lists,
        flat_tokens=flat_tokens,
    )
