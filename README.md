# TEYZIX — AI-Powered Document Summarizer

> Task ID: AI-INT-1 · TEYZIX CORE · June 2026

A production-grade Flask web application that extracts key insights from long documents using classical NLP. Supports extractive summarisation via three algorithms, analytics visualisation, file upload (txt/pdf), and export (txt/pdf).

---

## Features

- **Three summarisation methods** — Frequency-based, TF-IDF, and Combined (weighted)
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

---

## Project Structure

```
TEYZIX/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Dev / Prod / Test configuration
│   ├── features/
│   │   ├── summarizer/          # Routes, service, schemas, exceptions
│   │   ├── preprocessor/        # Text cleaner, tokenizer, pipeline
│   │   ├── analytics/           # Frequency, keywords, sentence scoring
│   │   └── file_handler/        # Upload validator, reader, writer, routes
│   ├── core/
│   │   ├── algorithms/          # frequency_scorer, tfidf_scorer, sentence_ranker
│   │   └── nlp/                 # NLTK + spaCy model loader (singleton)
│   ├── static/css/              # themes.css, main.css
│   ├── static/js/               # theme.js, charts.js, main.js
│   └── templates/               # base.html, index.html, partials/
├── tests/                       # pytest test suite
├── samples/                     # 3 sample documents for demo
├── docs/
│   └── PROJECT_EXPLANATION.md  # Full technical walkthrough
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
| `POST` | `/api/upload` | Upload a .txt or .pdf file |
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

`method` options: `"frequency"`, `"tfidf"`, `"combined"`  
`ratio` range: `0.1` – `0.9`

### `/api/summarize` — Response

```json
{
  "success": true,
  "summary": "...",
  "original_word_count": 1200,
  "summary_word_count": 240,
  "compression_ratio": "80%",
  "analytics": {
    "top_words": [{ "word": "ai", "count": 12 }],
    "keywords": ["machine learning", "neural network"],
    "sentence_scores": [{ "sentence": "...", "score": 0.87, "label": "high" }]
  }
}
```

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
| NLP | NLTK 3.8, spaCy 3.7 |
| ML | scikit-learn (TF-IDF) |
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
| NLP preprocessing (25%) | Lowercasing, stopword removal, tokenisation, sentence segmentation |
| Summarisation logic (25%) | Frequency scorer, TF-IDF scorer, weighted sentence ranker with positional bias |
| Code structure (20%) | Feature-modular Flask app with blueprints, service layer, and config classes |
| Output quality (15%) | Original vs summary display, compression stats, adjustable ratio |
| Error handling (10%) | Custom exceptions, client + server validation, Flask error handlers |
| Documentation (5%) | README + full technical explanation in `docs/PROJECT_EXPLANATION.md` |

---

## Author

Developer · TEYZIX CORE · Task AI-INT-1
