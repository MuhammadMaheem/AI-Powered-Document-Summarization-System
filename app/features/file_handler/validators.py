"""
File upload validators.

Centralises all checks so the route layer stays thin.
"""

from flask import current_app
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"txt", "pdf"}


def allowed_extension(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_upload(file) -> str:
    if not file or not file.filename:
        raise ValueError("No file provided.")

    if not allowed_extension(file.filename):
        raise ValueError("Only .txt and .pdf files are accepted.")

    # Flask enforces MAX_CONTENT_LENGTH at the WSGI level, but we double-check
    # here for clearer error messages on oversized streams.
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    limit = current_app.config.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)
    if size > limit:
        mb = limit / (1024 * 1024)
        raise ValueError(f"File exceeds the {mb:.0f} MB limit.")

    return secure_filename(file.filename)
