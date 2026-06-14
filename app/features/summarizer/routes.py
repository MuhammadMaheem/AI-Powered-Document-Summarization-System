from flask import Blueprint, request, jsonify, render_template

from app.features.summarizer.schemas import SummarizeRequest
from app.features.summarizer.service import summarize
from app.features.summarizer.batch_service import BatchSummarizeRequest, summarize_batch
from app.features.summarizer.exceptions import SummarizationError, ValidationError

summarizer_bp = Blueprint("summarizer", __name__)


@summarizer_bp.route("/")
def index():
    return render_template("index.html")


@summarizer_bp.route("/api/summarize", methods=["POST"])
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
        return jsonify({"success": False, "error": f"Unexpected error: {exc}"}), 500


@summarizer_bp.route("/api/summarize-batch", methods=["POST"])
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
        return jsonify({"success": False, "error": f"Unexpected error: {exc}"}), 500
