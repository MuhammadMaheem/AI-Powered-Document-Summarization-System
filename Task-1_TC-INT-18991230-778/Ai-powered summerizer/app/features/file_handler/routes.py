import io
import logging
import os
from flask import Blueprint, request, jsonify, send_file, current_app

from app.extensions import limiter
from app.features.file_handler.validators import validate_upload
from app.features.file_handler.reader import read_file
from app.features.file_handler.writer import export_summary

logger = logging.getLogger(__name__)
file_bp = Blueprint("file", __name__)

_MAX_BATCH_FILES = 10


@file_bp.route("/api/upload", methods=["POST"])
@limiter.limit("30 per minute")
def upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file field in request."}), 400

    file = request.files["file"]

    try:
        safe_name = validate_upload(file)
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, safe_name)
    file.save(filepath)

    try:
        text = read_file(filepath)
    except Exception as exc:
        logger.warning("File read failed for %s: %s", safe_name, exc)
        return jsonify({"success": False, "error": f"Could not read file: {exc}"}), 422
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

    if not text.strip():
        return jsonify({"success": False, "error": "The file appears to be empty."}), 422

    return jsonify({"success": True, "text": text, "char_count": len(text)})


@file_bp.route("/api/upload-multiple", methods=["POST"])
@limiter.limit("10 per minute")
def upload_multiple():
    files = request.files.getlist("files")

    if not files or all(f.filename == "" for f in files):
        return jsonify({"success": False, "error": "No files received."}), 400

    if len(files) > _MAX_BATCH_FILES:
        return jsonify({
            "success": False,
            "error": f"Maximum {_MAX_BATCH_FILES} files per batch.",
        }), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    texts = []
    names = []
    char_counts = []
    errors = []

    for file in files:
        if file.filename == "":
            continue

        try:
            safe_name = validate_upload(file)
        except ValueError as exc:
            errors.append({"name": file.filename, "error": str(exc)})
            continue

        filepath = os.path.join(upload_folder, safe_name)
        file.save(filepath)

        try:
            text = read_file(filepath)
        except Exception as exc:
            logger.warning("Batch file read failed for %s: %s", file.filename, exc)
            errors.append({"name": file.filename, "error": f"Could not read file: {exc}"})
            continue
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

        if not text.strip():
            errors.append({"name": file.filename, "error": "File appears to be empty."})
            continue

        texts.append(text)
        names.append(file.filename)
        char_counts.append(len(text))

    if not texts:
        first_error = errors[0]["error"] if errors else "No valid files could be read."
        return jsonify({"success": False, "error": first_error}), 422

    return jsonify({
        "success": True,
        "texts": texts,
        "names": names,
        "char_counts": char_counts,
        "errors": errors,
    })


@file_bp.route("/api/export", methods=["POST"])
@limiter.limit("30 per minute")
def export():
    data = request.get_json(silent=True) or {}
    summary = data.get("summary", "").strip()
    fmt = data.get("format", "txt").lower()

    if not summary:
        return jsonify({"success": False, "error": "No summary provided."}), 400

    if fmt not in ("txt", "pdf"):
        return jsonify({"success": False, "error": "Format must be 'txt' or 'pdf'."}), 400

    try:
        file_bytes, filename = export_summary(summary, fmt)
    except Exception as exc:
        logger.error("Export failed: %s", exc)
        return jsonify({"success": False, "error": f"Export failed: {exc}"}), 500

    mime = "application/pdf" if fmt == "pdf" else "text/plain"
    return send_file(
        io.BytesIO(file_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype=mime,
    )


@file_bp.route("/api/health")
def health():
    return jsonify({"status": "ok"})
