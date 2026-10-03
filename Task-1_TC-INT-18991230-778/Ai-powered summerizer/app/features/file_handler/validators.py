from flask import current_app
from werkzeug.utils import secure_filename

_PDF_MAGIC = b"%PDF"


def _allowed_extension(filename: str, allowed: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _check_pdf_magic(file) -> bool:
    header = file.read(4)
    file.seek(0)
    return header == _PDF_MAGIC


def validate_upload(file) -> str:
    if not file or not file.filename:
        raise ValueError("No file provided.")

    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"txt", "pdf"})

    if not _allowed_extension(file.filename, allowed):
        raise ValueError(f"Only {', '.join(f'.{e}' for e in sorted(allowed))} files are accepted.")

    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext == "pdf" and not _check_pdf_magic(file):
        raise ValueError("File does not appear to be a valid PDF.")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    limit = current_app.config.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)
    if size > limit:
        mb = limit / (1024 * 1024)
        raise ValueError(f"File exceeds the {mb:.0f} MB limit.")

    return secure_filename(file.filename)
