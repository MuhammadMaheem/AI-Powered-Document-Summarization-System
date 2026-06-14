# TEYZIX — AI-Powered Document Summarizer

> Task ID: AI-INT-1 · TEYZIX CORE · June 2026

A production-grade Flask web application that extracts key insights from long documents using classical NLP and optional deep-learning abstractive summarization. Supports four summarisation methods, multi-document processing, language detection, analytics visualisation, file upload (txt/pdf), and export (txt/pdf).

---

## Features

- **Four summarisation methods:**
  - **Frequency-based** — scores sentences by word occurrence count
  - **TF-IDF** — scores sentences using term frequency–inverse document frequency
  - **Combined** — weighted blend of both + positional bias (recommended)
  - **Abstractive (BART)** — deep-learning model generates brand-new sentences (optional, requires `transformers` + `torch`)
- **Language detection** — auto-detects 16 languages, applies language-specific stopwords
- **Multi-document summarization** — upload up to 10 files, Combined or Individual mode
- **PDF + TXT upload** — Drag-and-drop or file browser
- **Adjustable summary length** — 10% to 90% slider
- **Analytics panel** — Top keywords, word frequency chart (Chart.js), sentence importance scores
- **Export** — Download summary as `.txt` or `.pdf`
- **Dark / light mode** — Persists across sessions via localStorage
- **Input validation** — Client-side + server-side, 100–50,000 character limits

---

## Quick Start

```bash
# 1. Clone
git clone <your-repo-url> TEYZIX
cd TEYZIX

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies and download NLP models
make setup

# 4. Copy and configure environment
cp .env.example .env

# 5. Run development server
make run
# → open http://127.0.0.1:5000
```

Or without Make:

```bash
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"
python -m spacy download en_core_web_sm
python run.py
```

### Abstractive Summarization (BART)

`transformers` and `torch` are included in `requirements.txt`. The BART model (`facebook/bart-large-cnn`, ~1.6 GB) downloads automatically on first use. Requires ~4 GB RAM.

```bash
# already installed via make setup / pip install -r requirements.txt
```

Select **"Abstractive — BART ✦"** from the method dropdown. First run triggers a one-time model download — subsequent runs are instant.

---

## Project Structure

```
TEYZIX/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Dev / Prod / Test configuration
│   ├── features/
│   │   ├── summarizer/          # Routes, service, schemas, exceptions, batch_service
│   │   ├── preprocessor/        # Text cleaner, tokenizer, pipeline, language_detector
│   │   ├── analytics/           # Frequency, keywords, sentence scoring
│   │   └── file_handler/        # Upload validator, reader, writer, routes
│   ├── core/
│   │   ├── algorithms/          # frequency_scorer, tfidf_scorer, sentence_ranker
│   │   │                        # abstractive_summarizer (BART — optional)
│   │   └── nlp/                 # NLTK + spaCy model loader (singleton)
│   ├── static/css/              # themes.css, main.css
│   ├── static/js/               # theme.js, charts.js, main.js
│   └── templates/               # base.html, index.html, partials/
├── tests/                       # pytest test suite (22 tests)
├── samples/                     # 3 sample documents for demo
├── docs/
│   └── PROJECT_EXPLANATION.md  # Full technical walkthrough + interview Q&A
├── run.py                       # Development entry point
├── wsgi.py                      # Production (Gunicorn) entry point
├── requirements.txt
└── Makefile
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Main UI page |
| `POST` | `/api/summarize` | Summarise text (JSON body) |
| `POST` | `/api/summarize-batch` | Summarise multiple documents |
| `POST` | `/api/upload` | Upload a .txt or .pdf file |
| `POST` | `/api/upload-multiple` | Upload multiple files (batch) |
| `POST` | `/api/export` | Download summary as .txt or .pdf |
| `GET`  | `/api/health` | Health check |

### `/api/summarize` — Request body

```json
{
  "text": "your document text here...",
  "method": "combined",
  "ratio": 0.3
}
```

`method` options: `"frequency"`, `"tfidf"`, `"combined"`, `"abstractive"`  
`ratio` range: `0.1` – `0.9`

### `/api/summarize` — Response

```json
{
  "success": true,
  "summary": "...",
  "summary_type": "extractive",
  "original_word_count": 1200,
  "summary_word_count": 240,
  "compression_ratio": "80%",
  "detected_language": "en",
  "detected_language_name": "English",
  "analytics": {
    "top_words": [{ "word": "ai", "count": 12 }],
    "keywords": ["machine learning", "neural network"],
    "sentence_scores": [{ "sentence": "...", "score": 0.87, "label": "high" }]
  }
}
```

### `/api/summarize-batch` — Request body

```json
{
  "documents": ["text of doc 1...", "text of doc 2..."],
  "names": ["report.pdf", "email.txt"],
  "method": "combined",
  "ratio": 0.3,
  "mode": "combined"
}
```

`mode` options: `"combined"` (one merged summary), `"individual"` (separate summary per doc)  
Maximum 10 documents per request.

---

## Running Tests

```bash
make test
# or
python -m pytest tests/ -v
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Web framework | Flask 3.0 |
| NLP | NLTK 3.8, spaCy 3.8 |
| ML | scikit-learn (TF-IDF) |
| Language detection | langdetect |
| Deep learning (optional) | HuggingFace Transformers, PyTorch — `facebook/bart-large-cnn` |
| PDF read | pdfplumber |
| PDF export | reportlab |
| Frontend | Vanilla JS, Chart.js |
| Font | Inter (Google Fonts) |
| Production server | Gunicorn |

---

## Production Deployment

```bash
gunicorn wsgi:app --workers 4 --bind 0.0.0.0:8000
```

---

## Evaluation Criteria Coverage

| Criterion | Implementation |
|-----------|---------------|
| NLP preprocessing (25%) | Lowercasing, stopword removal, tokenisation, sentence segmentation, language detection (16 languages) |
| Summarisation logic (25%) | Frequency scorer, TF-IDF scorer, weighted ranker with positional bias, BART abstractive summarization |
| Code structure (20%) | Feature-modular Flask app with blueprints, service layer, config classes, singleton model loaders |
| Output quality (15%) | Original vs summary display, compression stats, adjustable ratio, analytics panel, language badge |
| Error handling (10%) | Custom exceptions, client + server validation, Flask error handlers, graceful BART fallback |
| Documentation (5%) | README + full technical explanation in `docs/PROJECT_EXPLANATION.md` (includes interview Q&A) |

### Bonus Challenges Completed

| Bonus | Status |
|-------|--------|
| Abstractive summarization (BART) | ✅ Implemented — optional install |
| Language detection | ✅ 16 languages supported |
| Multi-document summarization | ✅ Combined + Individual modes, up to 10 docs |

---

## Author

Developer · TEYZIX CORE · Task AI-INT-1
# AI-Powered-Document-Summarization-System
