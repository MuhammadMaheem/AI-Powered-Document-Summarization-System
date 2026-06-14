"""
Abstractive summarization using facebook/bart-large-cnn.

Unlike extractive methods (frequency, TF-IDF) which select existing
sentences, BART generates brand-new sentences by understanding the
document semantically — like a human rewriting the content.

Long document handling (chunking + hierarchical):
  BART has a hard limit of 1024 tokens (~800 words). For longer texts:
  1. Split into ~800-word chunks
  2. Summarize each chunk — each chunk's target is a proportional share
     of the total desired summary length (avoids double compression)
  3. Concatenate chunk summaries
  4. Only run a hierarchical second pass if the combined chunk summaries
     are still significantly longer than the final target

Note on transformers v5:
  The 'summarization' pipeline task was removed in transformers 5.x.
  We use BartTokenizer + BartForConditionalGeneration directly.
"""

import re
import threading
from typing import Optional

_lock = threading.Lock()
_model = None
_tokenizer = None
_available: Optional[bool] = None

MODEL_ID = "facebook/bart-large-cnn"
MAX_WORDS_PER_CHUNK = 800
MAX_TOKENS = 1024

# BART token-to-word ratio: ~1.3 BART tokens per word
TOKENS_PER_WORD = 1.3


class AbstractiveNotAvailable(Exception):
    pass


def _load_model() -> None:
    global _model, _tokenizer, _available
    try:
        from transformers import BartTokenizer, BartForConditionalGeneration  # type: ignore
        _tokenizer = BartTokenizer.from_pretrained(MODEL_ID)
        _model = BartForConditionalGeneration.from_pretrained(MODEL_ID)
        _available = True
    except ImportError:
        _available = False
        raise AbstractiveNotAvailable(
            "Abstractive summarization requires transformers and torch. "
            "Install them: pip install transformers torch"
        )
    except Exception as exc:
        _available = False
        raise AbstractiveNotAvailable(f"Could not load BART model: {exc}")


def _get_model():
    global _model, _tokenizer
    if _available is False:
        raise AbstractiveNotAvailable(
            "Abstractive summarization is not available. "
            "Install: pip install transformers torch"
        )
    if _model is not None:
        return _model, _tokenizer
    with _lock:
        if _model is None:
            _load_model()
    return _model, _tokenizer


def _words_to_tokens(word_count: int) -> int:
    return round(word_count * TOKENS_PER_WORD)


def _summarize_chunk(text: str, min_len: int, max_len: int) -> str:
    import torch  # type: ignore
    model, tokenizer = _get_model()
    inputs = tokenizer(
        text,
        return_tensors="pt",
        max_length=MAX_TOKENS,
        truncation=True,
    )
    with torch.no_grad():
        ids = model.generate(
            inputs["input_ids"],
            min_length=min_len,
            max_length=max_len,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True,
            no_repeat_ngram_size=3,
        )
    return tokenizer.decode(ids[0], skip_special_tokens=True)


def _trim_to_sentence(text: str) -> str:
    """Trim text to the last complete sentence so output never cuts mid-sentence."""
    match = re.search(r'[.!?](?:\s|$)', text)
    if not match:
        return text.strip()
    # Find the last sentence-ending punctuation
    last = max(
        (m.end() for m in re.finditer(r'[.!?](?:\s|$)', text)),
        default=len(text),
    )
    return text[:last].strip()


def _chunk_text(text: str, max_words: int = MAX_WORDS_PER_CHUNK) -> list:
    words = text.split()
    return [
        " ".join(words[i:i + max_words])
        for i in range(0, len(words), max_words)
    ]


def summarize_abstractive(text: str, ratio: float = 0.3) -> str:
    chunks = _chunk_text(text)
    original_wc = len(text.split())
    n_chunks = len(chunks)

    # Total desired words in final output
    target_final_words = max(50, round(ratio * original_wc))

    chunk_summaries = []
    for chunk in chunks:
        chunk_wc = len(chunk.split())

        # Each chunk's target = proportional share of total desired output.
        # Clamp to BART's realistic per-chunk range (40–180 words).
        words_per_chunk_target = max(40, min(180, round(target_final_words / n_chunks)))

        # Convert word targets to BART token counts
        min_len = max(30, _words_to_tokens(round(words_per_chunk_target * 0.65)))
        max_len = min(280, _words_to_tokens(words_per_chunk_target) + 60)

        chunk_summaries.append(_summarize_chunk(chunk, min_len, max_len))

    if n_chunks == 1:
        return _trim_to_sentence(chunk_summaries[0])

    combined = " ".join(chunk_summaries)
    combined_wc = len(combined.split())

    # Only do a second hierarchical pass if combined summaries are still
    # more than 1.5× the final target — avoids double-compression.
    if combined_wc > target_final_words * 1.5:
        min_len = max(40, _words_to_tokens(round(target_final_words * 0.65)))
        max_len = min(512, _words_to_tokens(target_final_words) + 60)
        result = _summarize_chunk(combined, min_len=min_len, max_len=max_len)
        return _trim_to_sentence(result)

    return _trim_to_sentence(combined)
