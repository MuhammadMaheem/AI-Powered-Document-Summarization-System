import logging
from flask import Blueprint, request, jsonify, render_template

from app.extensions import limiter
from app.features.summarizer.schemas import SummarizeRequest
from app.features.summarizer.service import summarize
from app.features.summarizer.batch_service import BatchSummarizeRequest, summarize_batch
from app.features.summarizer.exceptions import SummarizationError, ValidationError

logger = logging.getLogger(__name__)


def _map_to_ui_shape(d: dict, method: str, ratio: float) -> dict:
    """Map service response → shape expected by the v2 frontend."""
    top_words = d["analytics"]["top_words"]
    raw_scores = d["analytics"]["sentence_scores"]  # [{sentence, score, rank, label}]
    summary_text = d["summary"]

    sentence_scores = [
        {
            "rank": ss["rank"],
            "text": ss["sentence"],
            "label": ss["label"],
            "score": round(ss["score"] * 100),
            "inSummary": ss["sentence"] in summary_text,
        }
        for ss in raw_scores
    ]
    sentence_scores.sort(key=lambda x: x["rank"])

    comp_str = d.get("compression_ratio", "0%")
    compression = int(comp_str.rstrip("%")) if isinstance(comp_str, str) and comp_str.endswith("%") else 0

    sum_sentences = sum(1 for s in sentence_scores if s["inSummary"])
    reading_time = max(1, round(d["summary_word_count"] / 200))

    lang_name = d.get("detected_language_name", "English")
    lang_code = (d.get("detected_language", "en") or "en").upper()[:2]

    keywords = top_words[:14]

    return {
        "language": {"name": lang_name, "code": lang_code, "conf": 80},
        "summaryText": summary_text,
        "keywords": keywords,
        "keywordWords": [k["word"] for k in keywords],
        "chart": top_words[:8],
        "sentenceScores": sentence_scores,
        "stats": {
            "origWords": d["original_word_count"],
            "sumWords": d["summary_word_count"],
            "compression": compression,
            "origSentences": len(raw_scores),
            "sumSentences": sum_sentences,
            "readingTime": reading_time,
        },
    }


summarizer_bp = Blueprint("summarizer", __name__)


@summarizer_bp.route("/")
def index():
    return render_template("index.html")


@summarizer_bp.route("/api/summarize", methods=["POST"])
@limiter.limit("15 per minute")
def summarize_route():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Request body must be JSON."}), 400

    try:
        req = SummarizeRequest.from_dict(data)
        response = summarize(req)
        return jsonify(response.to_dict())
    except ValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 422
    except SummarizationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 422
    except Exception as exc:
        logger.exception("Unexpected error in /api/summarize")
        return jsonify({"success": False, "error": f"Unexpected error: {exc}"}), 500


@summarizer_bp.route("/summarize", methods=["POST"])
@limiter.limit("15 per minute")
def summarize_v2():
    """New-design endpoint: accepts {docs, method, ratio}, returns UI-shaped JSON."""
    data = request.get_json(silent=True) or {}
    docs = data.get("docs", [])
    method = data.get("method", "combined")
    ratio = float(data.get("ratio", 0.4))

    full_text = "\n\n".join(d.get("text", "") for d in docs if d.get("text", "").strip())
    if not full_text.strip():
        return jsonify({"error": "empty"}), 400

    try:
        req = SummarizeRequest.from_dict({"text": full_text, "method": method, "ratio": ratio})
        resp = summarize(req)
        result = _map_to_ui_shape(resp.to_dict(), method, ratio)
        return jsonify(result)
    except (SummarizationError, ValidationError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("Unexpected error in /summarize")
        return jsonify({"error": f"Unexpected error: {exc}"}), 500


@summarizer_bp.route("/api/summarize-batch", methods=["POST"])
@limiter.limit("5 per minute")
def summarize_batch_route():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Request body must be JSON."}), 400

    try:
        req = BatchSummarizeRequest.from_dict(data)
        response = summarize_batch(req)
        return jsonify(response)
    except ValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 422
    except SummarizationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 422
    except Exception as exc:
        logger.exception("Unexpected error in /api/summarize-batch")
        return jsonify({"success": False, "error": f"Unexpected error: {exc}"}), 500
