"""
File reading utilities.

Supports plain text (.txt) and PDF (.pdf) files.
PDF text is extracted page-by-page using pdfplumber.
"""

import os
import pdfplumber


def read_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def read_pdf(filepath: str) -> str:
    pages = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def read_file(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".txt":
        return read_txt(filepath)
    if ext == ".pdf":
        return read_pdf(filepath)
    raise ValueError(f"Unsupported file extension: {ext}")
