# TEYZIX — AI-Powered Document Summarizer

A Flask web application that distills long documents into concise summaries using classical NLP and optional deep-learning abstractive summarization. Supports four summarization methods, multi-document batch processing, 16-language detection, analytics visualization, file upload, and export.

---

## Features

- **Four summarization methods**
  - **Frequency** — scores sentences by word occurrence count
  - **TF-IDF** — scores by term frequency–inverse document frequency
  - **Combined** — weighted blend of both with positional bias (recommended default)
  - **Abstractive (BART)** — `facebook/bart-large-cnn` generates new sentences; chunked for long documents
- **Language detection** — auto-detects 16 languages; applies language-specific stopwords
- **Batch processing** — up to 10 documents per request, Combined or Individual mode
- **File upload** — `.txt` and `.pdf`, validated by extension and magic bytes, up to 5 MB
- **Export** — download summary as `.txt` or `.pdf` (served from memory, no disk residue)
- **Analytics panel** — top keywords, word frequency chart, per-sentence importance scores
- **Rate limiting** — per-IP limits on all write endpoints via Flask-Limiter
- **CORS** — configurable origins via environment variable
- **Dark / light theme** — persists across sessions via localStorage
- **Adjustable ratio** — 10%–90% summary length slider

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Flask 3.0 |
| NLP | NLTK 3.8, spaCy 3.8 (`en_core_web_sm`) |
| Scoring | scikit-learn TF-IDF |
| Abstractive model | `facebook/bart-large-cnn` (HuggingFace Transformers) |
| Language detection | langdetect |
| PDF read | pdfplumber |
| PDF export | reportlab |
| Rate limiting | Flask-Limiter |
| CORS | Flask-CORS |
| Frontend | Vanilla JS, Chart.js |
| Production server | Gunicorn |

---

## Project Structure

```
TEYZIX/
├── app/
│   ├── __init__.py              # App factory — CORS, rate limiting, logging, NLP init
│   ├── config.py                # Dev / Prod / Testing config classes
│   ├── extensions.py            # Flask-Limiter singleton
│   ├── core/
│   │   ├── algorithms/
│   │   │   ├── frequency_scorer.py
│   │   │   ├── tfidf_scorer.py
│   │   │   ├── sentence_ranker.py
│   │   │   └── abstractive_summarizer.py  # BART with chunked long-doc support
│   │   └── nlp/
│   │       └── model_loader.py  # NLTK + spaCy singletons, lazy init
│   ├── features/
│   │   ├── analytics/           # top_words, keywords, sentence scoring
│   │   ├── file_handler/        # upload validator (magic-byte), reader, in-memory export
│   │   ├── preprocessor/        # pipeline, tokenizer, cleaner, language detector
│   │   └── summarizer/          # routes, service, schemas, batch service, exceptions
│   ├── static/
│   │   ├── app.js
│   │   └── styles.css
│   └── templates/
│       └── index.html
├── tests/
│   ├── test_analytics.py        # 5 tests
│   ├── test_preprocessor.py     # 8 tests
│   └── test_summarizer.py       # 9 tests
├── samples/                     # Sample .txt documents for testing
├── run.py                       # Dev entry point (debug off by default)
├── wsgi.py                      # Production WSGI entry point (Gunicorn)
├── Makefile
└── requirements.txt
```

---

## Quick Start

### 1. Clone and create a virtual environment

```bash
git clone <repo-url> TEYZIX
cd TEYZIX
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
```

### 2. Install dependencies and NLP models

```bash
make setup
```

This runs `pip install -r requirements.txt` and downloads NLTK corpora plus the spaCy English model.

### 3. Configure environment

Create a `.env` file in the project root:

```bash
SECRET_KEY=your-secure-random-key
FLASK_ENV=development
FLASK_DEBUG=false
```

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(required in production)* | Flask secret key for session signing |
| `FLASK_ENV` | `development` | `development` / `production` / `testing` |
| `FLASK_DEBUG` | `false` | Set `true` to enable Werkzeug debugger |
| `CORS_ORIGINS` | `*` | Allowed origins (e.g. `https://yourapp.com`) |
| `MAX_UPLOAD_BYTES` | `5242880` | Upload size limit in bytes (default 5 MB) |
| `MAX_BATCH_COMBINED_CHARS` | `150000` | Max characters for batch-combined mode |

### 4. Run

```bash
make run
# or
python run.py
```

Open `http://127.0.0.1:5001`.

### Production

```bash
gunicorn wsgi:app --workers 4 --bind 0.0.0.0:8000
```

Set `SECRET_KEY` via environment variable — the app raises a `RuntimeError` at startup if it is not configured in production mode.

### Abstractive Summarization (BART)

The `facebook/bart-large-cnn` model (~1.6 GB) downloads automatically on first use. Requires ~4 GB RAM. Select **"Abstractive — BART ✦"** in the method dropdown. Subsequent runs use the cached model.

---

## API Reference

All endpoints return JSON. Rate limits apply per IP address.

### `POST /api/summarize`

**Rate limit:** 15 req/min

**Request:**

```json
{
  "text": "Your document text...",
  "method": "combined",
  "ratio": 0.3
}
```

| Field | Type | Values | Default |
|---|---|---|---|
| `text` | string | 100–50,000 characters | required |
| `method` | string | `frequency` / `tfidf` / `combined` / `abstractive` | `combined` |
| `ratio` | float | 0.1–0.9 | `0.3` |

**Response:**

```json
{
  "success": true,
  "summary": "...",
  "summary_type": "extractive",
  "original_word_count": 420,
  "summary_word_count": 126,
  "compression_ratio": "70%",
  "detected_language": "en",
  "detected_language_name": "English",
  "analytics": {
    "top_words": [{"word": "summarization", "count": 5}],
    "keywords": ["extractive summarization", "sentence scoring"],
    "sentence_scores": [
      {"sentence": "...", "score": 0.85, "rank": 1, "label": "high"}
    ]
  }
}
```

`label` values are rank-based: top 33% = `high`, middle 33% = `medium`, bottom 33% = `low`.

---

### `POST /api/summarize-batch`

**Rate limit:** 5 req/min

```json
{
  "documents": ["Doc 1 text...", "Doc 2 text..."],
  "names": ["report.pdf", "email.txt"],
  "method": "combined",
  "ratio": 0.3,
  "mode": "individual"
}
```

| Field | Values | Notes |
|---|---|---|
| `mode` | `combined` / `individual` | Combined merges all docs into one summary |
| `method` | `frequency` / `tfidf` / `combined` | Abstractive not supported in batch |
| Max documents | 10 | Per request |
| Max combined text | 150K chars | For `combined` mode only |

---

### `POST /api/upload`

**Rate limit:** 30 req/min

Upload a single `.txt` or `.pdf` file (multipart, field name `file`). File is validated by extension and PDF magic bytes, read into memory, then deleted from disk.

```json
{"success": true, "text": "...", "char_count": 3842}
```

---

### `POST /api/upload-multiple`

**Rate limit:** 10 req/min

Upload up to 10 files (field name `files`). Returns texts with per-file errors for partial failures.

---

### `POST /api/export`

**Rate limit:** 30 req/min

```json
{"summary": "Summary text...", "format": "txt"}
```

`format`: `txt` or `pdf`. File is generated in memory and returned as an attachment — nothing is written to disk.

---

### `GET /api/health`

```json
{"status": "ok"}
```

---

## Running Tests

```bash
make test
# or
python -m pytest tests/ -v
```

22 tests covering analytics, preprocessor pipeline, and summarizer routes.

---

## Security

| Control | Implementation |
|---|---|
| File type validation | Extension check + `%PDF` magic-byte check |
| Upload cleanup | Files deleted from disk immediately after text extraction |
| Export | Generated in memory — no files written to disk |
| Rate limiting | Per-IP limits on all write endpoints (Flask-Limiter) |
| CORS | Configurable via `CORS_ORIGINS` env var (default `*`) |
| Secret key | Must be set via env var in production — app refuses to start otherwise |
| Debug mode | Off by default; enable only with `FLASK_DEBUG=true` |

---

## Makefile Targets

| Target | Description |
|---|---|
| `make install` | Install Python dependencies |
| `make setup` | Install deps + download NLP models |
| `make run` | Start development server |
| `make test` | Run test suite |
| `make clean` | Remove `__pycache__` and `.pyc` files |

---

## Author

Muhammad Maheem — TEYZIX CORE — Task AI-INT-1
