"""
Batch summarization service.

Handles multiple documents in one request with two modes:
- combined:    concatenate all texts, produce one summary
- individual:  summarize each document separately, return array of results

Validation mirrors SummarizeRequest limits (100 char min, 50k char max
per document) so every document is independently validated before any
processing starts.

Note: abstractive method is excluded from batch because BART inference
on many large documents can be prohibitively slow (minutes per request).
"""

import logging
from dataclasses import dataclass, field
from typing import List

from flask import current_app

from app.features.summarizer.service import summarize
from app.features.summarizer.schemas import SummarizeRequest, VALID_METHODS
from app.features.summarizer.exceptions import ValidationError

logger = logging.getLogger(__name__)

BATCH_VALID_METHODS = tuple(m for m in VALID_METHODS if m != "abstractive")
MAX_DOCUMENTS = 10


@dataclass
class BatchSummarizeRequest:
    documents: List[str]
    names: List[str]
    method: str = "combined"
    ratio: float = 0.3
    mode: str = "combined"

    @classmethod
    def from_dict(cls, data: dict) -> "BatchSummarizeRequest":
        docs = data.get("documents") or []
        names = data.get("names") or []

        if not isinstance(docs, list) or len(docs) == 0:
            raise ValidationError("documents must be a non-empty list.")
        if len(docs) > MAX_DOCUMENTS:
            raise ValidationError(f"Maximum {MAX_DOCUMENTS} documents per batch.")

        min_len = current_app.config.get("MIN_TEXT_LENGTH", 100)
        max_len = current_app.config.get("MAX_TEXT_LENGTH", 50_000)

        for i, doc in enumerate(docs):
            label = names[i] if i < len(names) else f"Document {i + 1}"
            if not isinstance(doc, str) or len(doc.strip()) < min_len:
                raise ValidationError(f"{label}: text must be at least {min_len} characters.")
            if len(doc) > max_len:
                raise ValidationError(f"{label}: text exceeds {max_len} characters.")

        method = (data.get("method") or "combined").lower()
        if method not in BATCH_VALID_METHODS:
            raise ValidationError(
                f"method must be one of: {', '.join(BATCH_VALID_METHODS)} "
                f"(abstractive is not supported for batch requests)."
            )

        min_ratio = current_app.config.get("MIN_SUMMARY_RATIO", 0.1)
        max_ratio = current_app.config.get("MAX_SUMMARY_RATIO", 0.9)
        ratio = float(data.get("ratio", 0.3))
        if not (min_ratio <= ratio <= max_ratio):
            raise ValidationError(f"ratio must be between {min_ratio} and {max_ratio}.")

        mode = (data.get("mode") or "combined").lower()
        if mode not in ("combined", "individual"):
            raise ValidationError("mode must be 'combined' or 'individual'.")

        padded_names = [
            names[i] if i < len(names) else f"Document {i + 1}"
            for i in range(len(docs))
        ]

        return cls(
            documents=docs,
            names=padded_names,
            method=method,
            ratio=ratio,
            mode=mode,
        )


def summarize_batch(req: BatchSummarizeRequest) -> dict:
    if req.mode == "combined":
        combined_text = "\n\n".join(req.documents)

        max_combined = current_app.config.get("MAX_BATCH_COMBINED_CHARS", 150_000)
        if len(combined_text) > max_combined:
            raise ValidationError(
                f"Combined text exceeds {max_combined // 1000}K characters. "
                "Reduce document count or length, or use individual mode."
            )

        logger.info("Batch combined: %d docs, %d chars", len(req.documents), len(combined_text))
        result = summarize(
            SummarizeRequest.from_dict({
                "text": combined_text,
                "method": req.method,
                "ratio": req.ratio,
            })
        )
        response = result.to_dict()
        response["mode"] = "combined"
        response["document_count"] = len(req.documents)
        response["document_names"] = req.names
        return response

    # individual mode
    logger.info("Batch individual: %d docs", len(req.documents))
    results = []
    for i, doc in enumerate(req.documents):
        try:
            r = summarize(
                SummarizeRequest.from_dict({
                    "text": doc,
                    "method": req.method,
                    "ratio": req.ratio,
                })
            )
            entry = r.to_dict()
            entry["doc_index"] = i
            entry["doc_name"] = req.names[i]
        except Exception as exc:
            logger.warning("Batch doc %d failed: %s", i, exc)
            entry = {
                "success": False,
                "doc_index": i,
                "doc_name": req.names[i],
                "error": str(exc),
            }
        results.append(entry)

    return {
        "success": True,
        "mode": "individual",
        "document_count": len(req.documents),
        "results": results,
    }
