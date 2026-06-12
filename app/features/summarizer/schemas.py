"""
Input / output data structures and validation for the summariser.
"""

from dataclasses import dataclass
from typing import List, Optional
from flask import current_app

from app.features.summarizer.exceptions import TextTooShortError, TextTooLongError, ValidationError

VALID_METHODS = ("frequency", "tfidf", "combined")


@dataclass
class SummarizeRequest:
    text: str
    method: str
    ratio: float

    @classmethod
    def from_dict(cls, data: dict) -> "SummarizeRequest":
        text = (data.get("text") or "").strip()
        method = (data.get("method") or "combined").lower()
        ratio = float(data.get("ratio", 0.3))

        min_len = current_app.config.get("MIN_TEXT_LENGTH", 100)
        max_len = current_app.config.get("MAX_TEXT_LENGTH", 50_000)
        min_ratio = current_app.config.get("MIN_SUMMARY_RATIO", 0.1)
        max_ratio = current_app.config.get("MAX_SUMMARY_RATIO", 0.9)

        if len(text) < min_len:
            raise TextTooShortError(f"Text must be at least {min_len} characters.")
        if len(text) > max_len:
            raise TextTooLongError(f"Text must not exceed {max_len} characters.")
        if method not in VALID_METHODS:
            raise ValidationError(f"Method must be one of: {', '.join(VALID_METHODS)}.")
        if not (min_ratio <= ratio <= max_ratio):
            raise ValidationError(f"Ratio must be between {min_ratio} and {max_ratio}.")

        return cls(text=text, method=method, ratio=ratio)


@dataclass
class SummarizeResponse:
    summary: str
    original_word_count: int
    summary_word_count: int
    compression_ratio: str
    top_words: List[dict]
    keywords: List[str]
    sentence_scores: List[dict]

    def to_dict(self) -> dict:
        return {
            "success": True,
            "summary": self.summary,
            "original_word_count": self.original_word_count,
            "summary_word_count": self.summary_word_count,
            "compression_ratio": self.compression_ratio,
            "analytics": {
                "top_words": self.top_words,
                "keywords": self.keywords,
                "sentence_scores": self.sentence_scores,
            },
        }
