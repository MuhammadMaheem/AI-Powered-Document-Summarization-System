"""
Language detection for incoming text.

Uses langdetect to identify the ISO 639-1 code and maps it to
the NLTK stopwords corpus name so the preprocessor can apply
language-appropriate stopword removal.

Falls back to English on any detection failure — never raises.
"""

from langdetect import detect, LangDetectException

NLTK_LANG_MAP = {
    "en": "english",
    "fr": "french",
    "de": "german",
    "es": "spanish",
    "it": "italian",
    "pt": "portuguese",
    "nl": "dutch",
    "ru": "russian",
    "ar": "arabic",
    "fi": "finnish",
    "da": "danish",
    "hu": "hungarian",
    "nb": "norwegian",
    "ro": "romanian",
    "sv": "swedish",
    "tr": "turkish",
}

LANG_LABELS = {
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ru": "Russian",
    "ar": "Arabic",
    "fi": "Finnish",
    "da": "Danish",
    "hu": "Hungarian",
    "nb": "Norwegian",
    "ro": "Romanian",
    "sv": "Swedish",
    "tr": "Turkish",
}


def detect_language(text: str) -> tuple:
    """Return (iso_code, nltk_language_name, label).

    Samples the first 500 chars for speed.  On any error returns
    ("en", "english", "English").
    """
    try:
        code = detect(text[:500])
        nltk_name = NLTK_LANG_MAP.get(code, "english")
        label = LANG_LABELS.get(code, code.upper())
        return code, nltk_name, label
    except LangDetectException:
        return "en", "english", "English"
