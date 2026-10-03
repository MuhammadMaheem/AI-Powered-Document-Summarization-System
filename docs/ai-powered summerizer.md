# TEYZIX — Complete Technical Explanation

> For presentation use. Every module, function, design decision, and algorithm explained in plain language.

---

## Table of Contents

1. [What This Project Does](#1-what-this-project-does)
2. [Why Flask (Not FastAPI or Django)](#2-why-flask)
3. [Folder Structure Philosophy](#3-folder-structure-philosophy)
4. [The NLP Pipeline — Step by Step](#4-the-nlp-pipeline)
5. [Algorithm 1: Frequency-Based Scoring](#5-frequency-based-scoring)
6. [Algorithm 2: TF-IDF Scoring](#6-tfidf-scoring)
7. [Algorithm 3: Sentence Ranker with Positional Bias](#7-sentence-ranker)
8. [Algorithm 4: Abstractive Summarization (BART)](#8-abstractive-summarization)
9. [Language Detection](#9-language-detection)
10. [Multi-Document Summarization](#10-multi-document-summarization)
11. [Analytics Module](#11-analytics-module)
12. [File Handling (Upload + Export)](#12-file-handling)
13. [Flask Architecture (Blueprints + App Factory)](#13-flask-architecture)
14. [Validation Layer](#14-validation-layer)
15. [Frontend Architecture](#15-frontend-architecture)
16. [Dark / Light Theme System](#16-dark-light-theme)
17. [Why NOT LangGraph](#17-why-not-langgraph)
18. [How to Run and Test](#18-how-to-run)
19. [Common Interview Questions and Answers](#19-interview-prep)

---

## 1. What This Project Does

TEYZIX is a web application that automatically **summarises long documents**. You give it a report, article, or email and it returns a shorter version that preserves the most important sentences.

This is called **extractive summarisation** — we do not rewrite the text, we *select* the most important original sentences.

The system does five things:
1. Cleans and tokenises the text (NLP preprocessing)
2. Scores each sentence by importance
3. Selects the top-N sentences and returns them in original order
4. Runs analytics (word frequency, keyword extraction, sentence scoring)
5. Serves the result through a web interface with export options

---

## 2. Why Flask

Flask was chosen because:
- **The task requires it** (specified in the requirements)
- Flask is a micro-framework — it gives you routing and request handling without forcing a specific project structure, so we can implement our own clean architecture
- It is easy to understand and explain during a presentation
- The lightweight nature means every line in the codebase has a clear purpose

**Why not Django?** Django is a batteries-included framework built for database-driven CMS-style apps. Our app has no database and needs no ORM, admin panel, or form framework.

**Why not FastAPI?** FastAPI is excellent for async APIs, but adds complexity (async/await, Pydantic models) that is unnecessary for a single-user summarisation tool.

---

## 3. Folder Structure Philosophy

The project uses **feature-modular architecture**. The codebase is divided by feature (what it does), not by type (models/, views/, utils/).

```
app/features/summarizer/   → everything about the summarisation feature
app/features/preprocessor/ → everything about text preprocessing
app/features/analytics/    → everything about analytics
app/features/file_handler/ → everything about file I/O
app/core/algorithms/       → pure algorithm implementations (no Flask dependency)
app/core/nlp/              → NLP model management
```

**Why this structure?**

If you need to modify how TF-IDF works, you go to `app/core/algorithms/tfidf_scorer.py`. One file. One concern. Nothing else is affected.

If you later want to add a new feature (e.g., multi-document comparison), you create `app/features/multi_doc/` and add it without touching anything else.

This is known as the **Single Responsibility Principle** and **Separation of Concerns** — each module does one thing and does it well.

**The `core/` vs `features/` distinction:**
- `core/` contains pure logic with no Flask imports. You could test these functions in a Python script with no web server.
- `features/` contains Flask-aware code (routes, request parsing, response formatting).

---

## 4. The NLP Pipeline

**File:** `app/features/preprocessor/pipeline.py`

The pipeline runs in four stages for every document:

### Stage 1: Sentence Segmentation
```python
sentences = nltk.sent_tokenize(text)
```
NLTK's Punkt tokeniser splits the document into individual sentences. It uses a statistical model trained to recognise abbreviations, decimal numbers, and other edge cases that could be mistaken for sentence boundaries.

**Example:**
- Input: `"Dr. Smith arrived at 5 p.m. He was tired."`
- Output: `["Dr. Smith arrived at 5 p.m.", "He was tired."]`

Without this, naively splitting on `.` would break abbreviations.

### Stage 2: Word Tokenisation
```python
tokens = nltk.word_tokenize(sentence)
```
Each sentence is split into individual word tokens. This handles contractions, punctuation attachment, and other edge cases.

**Example:**
- Input: `"It's a well-known fact."`
- Output: `["It", "'s", "a", "well-known", "fact", "."]`

### Stage 3: Token Filtering
```python
filtered = [t for t in tokens if t.isalpha() and len(t) > 1]
```
We keep only alphabetic tokens with length > 1. This removes:
- Punctuation (`.`, `,`, `!`)
- Numbers (`2026`, `5.3`)
- Single characters (`a`, `I`)

### Stage 4: Stopword Removal
```python
from nltk.corpus import stopwords
stop_words = set(stopwords.words("english"))
cleaned = [t for t in tokens if t not in stop_words]
```
Stopwords are common words that carry no meaning for summarisation: `the`, `is`, `at`, `which`, `on`. NLTK provides a list of 179 English stopwords.

After removal, only **meaningful content words** remain: nouns, verbs, adjectives.

**Why remove stopwords?** If we included stopwords, they would dominate frequency counts and inflate scores for sentences that happen to use common grammatical words rather than informative content words.

### Output Structure
```python
@dataclass
class PreprocessResult:
    raw_sentences: List[str]       # ["Dr. Smith arrived...", "He was tired."]
    token_lists: List[List[str]]   # [["dr", "smith", "arrived"], ["tired"]]
    flat_tokens: List[str]         # ["dr", "smith", "arrived", "tired"]
```

`raw_sentences` preserves original casing (used in the final output).
`token_lists` are cleaned tokens per sentence (used for scoring).
`flat_tokens` are all tokens combined (used for word frequency analysis).

---

## 5. Frequency-Based Scoring

**File:** `app/core/algorithms/frequency_scorer.py`

**Idea:** Words that appear frequently in a document are likely important. Sentences that contain many important words are likely important.

### Step 1: Count word occurrences
```python
from collections import Counter
raw_freq = Counter(all_tokens)
# {"machine": 15, "learning": 12, "data": 10, ...}
```

### Step 2: Normalise frequencies
```python
max_freq = max(raw_freq.values())  # 15
norm_freq = {word: count / max_freq for word, count in raw_freq.items()}
# {"machine": 1.0, "learning": 0.8, "data": 0.67, ...}
```

Normalisation brings all values into [0, 1]. This makes scores comparable regardless of document length.

### Step 3: Score each sentence
```python
score = sum(norm_freq.get(token, 0.0) for token in sentence_tokens)
```

A sentence with tokens `["machine", "learning", "data"]` gets score `1.0 + 0.8 + 0.67 = 2.47`.

### Step 4: Normalise sentence scores
```python
max_score = max(raw_scores)
scores = [s / max_score for s in raw_scores]  # range [0, 1]
```

**Weakness of this approach:** It favours documents where the same words repeat many times. A word like "important" that appears once might actually be more significant than "data" that appears 20 times in a technical report. TF-IDF addresses this.

---

## 6. TF-IDF Scoring

**File:** `app/core/algorithms/tfidf_scorer.py`

TF-IDF stands for **Term Frequency — Inverse Document Frequency**.

### The key insight

In frequency scoring, `data` scores high because it appears often in a technical document. But `data` appears in nearly every sentence, so it doesn't help us distinguish *which* sentences are most important.

TF-IDF penalises words that appear in many sentences (high document frequency). A word that appears 5 times in one sentence but rarely elsewhere scores much higher than a word that appears once in every sentence.

### TF (Term Frequency)
How often does this word appear in this sentence?
```
TF(word, sentence) = count of word in sentence / total words in sentence
```

### IDF (Inverse Document Frequency)
How rare is this word across all sentences?
```
IDF(word) = log(total sentences / sentences containing the word)
```

Words that appear in every sentence get IDF ≈ 0 (log(1) = 0).
Words that appear in only one sentence get high IDF.

### TF-IDF
```
TF-IDF(word, sentence) = TF × IDF
```

### Implementation with sklearn
```python
from sklearn.feature_extraction.text import TfidfVectorizer

# Each sentence is treated as a "document"
cleaned_sentences = [" ".join(tokens) for tokens in token_lists]
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(cleaned_sentences)

# Score each sentence = sum of TF-IDF weights of its terms
scores = tfidf_matrix.sum(axis=1).flatten()
```

`TfidfVectorizer` handles the mathematical computation. It returns a matrix where rows are sentences and columns are unique terms. Each cell contains the TF-IDF weight for that term in that sentence.

Row-wise sum gives the total TF-IDF importance score for each sentence.

---

## 7. Sentence Ranker

**File:** `app/core/algorithms/sentence_ranker.py`

### Combining the two scores
```python
combined = (freq_weight * freq_score) + (tfidf_weight * tfidf_score)
# default: 0.5 * freq + 0.5 * tfidf
```

The combined method uses both algorithms equally. You can adjust the weights — e.g., `0.3 * freq + 0.7 * tfidf` would rely more heavily on TF-IDF.

### Positional bias
Research in NLP shows that important information in real documents tends to appear at the **beginning** (abstract, introduction, executive summary) and at the **end** (conclusion, recommendations).

```python
POSITIONAL_BOOST = 0.1

if i in (0, 1) or i == n - 1:
    score = min(score + POSITIONAL_BOOST, 1.0)
```

Sentences at positions 0, 1, and the last position receive a 0.1 boost to their combined score. This simulates the human habit of starting a document with key points and ending with conclusions.

### Selecting top-N sentences
```python
num_sentences = max(1, round(ratio * n))
ranked = sorted(combined, key=lambda x: x["score"], reverse=True)
top = sorted(ranked[:num_sentences], key=lambda x: x["index"])
```

1. Sort all sentences by score descending
2. Take the top N (where N = ratio × total sentences)
3. Re-sort by original index to restore natural reading order

**Why re-sort?** If we returned sentences in score order, the summary would be scrambled. Re-sorting by `index` means the output reads as a coherent paragraph.

---

## 8. Abstractive Summarization (BART)

**File:** `app/core/algorithms/abstractive_summarizer.py`

### Extractive vs Abstractive — the key difference

All three previous algorithms are **extractive**: they pick and return sentences that already exist in the document. The output is always verbatim text from the source.

**Abstractive summarization** works differently. The model reads the entire document, understands its meaning, and then **generates brand-new sentences** that were never in the original text. The output can rephrase, combine, or condense ideas — just like a human would when summarizing in their own words.

Example:
- Input: `"The stock market fell sharply. Investors panicked. Trading volume hit record highs."`
- Extractive output: `"The stock market fell sharply. Trading volume hit record highs."` ← copied sentences
- Abstractive output: `"Market volatility triggered investor panic amid record trading activity."` ← new sentence

### What is BART?

BART stands for **Bidirectional and Auto-Regressive Transformer**. It was created by Facebook/Meta and has two components:

**Encoder** (bidirectional — like BERT):
- Reads the entire input text simultaneously in both directions
- Builds a deep contextual understanding of every word in relation to every other word
- Produces a compressed representation of the document's meaning

**Decoder** (auto-regressive — like GPT):
- Generates the summary one token (word-piece) at a time
- Each new token is conditioned on the encoder's representation AND all previously generated tokens
- Continues until an end-of-sequence token is generated or a length limit is reached

The model used is `facebook/bart-large-cnn`, pre-trained on 300,000 CNN and DailyMail news article–summary pairs. This means it is already an expert at summarizing news and reports out of the box — no fine-tuning required.

### Long document handling (chunking)

BART has a hard input limit of **1024 tokens** (~800 words). For longer documents, we use **hierarchical summarization**:

```
Step 1: Split text into 800-word chunks
        ["chunk 1...", "chunk 2...", "chunk 3..."]

Step 2: Summarize each chunk independently
        ["summary of chunk 1", "summary of chunk 2", "summary of chunk 3"]

Step 3: Concatenate chunk summaries
        "summary of chunk 1 summary of chunk 2 summary of chunk 3"

Step 4: Run BART again on the combined chunk summaries
        → Final summary
```

This approach preserves information from all parts of a long document.

### Ratio to length mapping

The user's ratio slider (0.1–0.9) is mapped to BART's `min_length` and `max_length` parameters:

```python
target_words = max(30, round(ratio * word_count))
min_length = max(20, round(target_words * 0.6))
max_length = target_words + 30
```

### Lazy loading and graceful fallback

The BART model (~1.6 GB) is **loaded on first request only** and cached in memory for subsequent requests. If `transformers` or `torch` are not installed, the system raises `AbstractiveNotAvailable` — a specific exception caught by the service layer and returned to the client as a clear 422 error. The other three methods continue working normally.

```python
_pipeline = None  # None until first abstractive request

def _get_pipeline():
    if _pipeline is None:
        _load_pipeline()  # downloads + loads model on first call
    return _pipeline
```

### Why BART and not other models?

| Model | Good for | Problem |
|-------|----------|---------|
| `facebook/bart-large-cnn` | Document summarization | ~1.6 GB |
| `google/pegasus-cnn_dailymail` | Summarization, similar quality | Similar size |
| `t5-small` | Many tasks, very small | Lower quality summaries |
| GPT-4 (API) | Everything | Costs money, needs internet |

BART-large-CNN is the industry standard for offline summarization — best quality-to-practicality ratio.

---

## 9. Language Detection

**File:** `app/features/preprocessor/language_detector.py`

### What it does

Before any preprocessing, the pipeline samples the first 500 characters of the input text and identifies the language using the `langdetect` library. It returns:
- An ISO 639-1 code (`"en"`, `"fr"`, `"de"`, `"es"`, etc.)
- The NLTK language name (`"english"`, `"french"`, etc.) used to select the correct stopword list
- A human-readable label (`"English"`, `"French"`) shown in the UI

### Why sample only 500 characters?

Language detection is statistical — it needs enough characters to make a reliable prediction but doesn't need the entire document. 500 characters (~3–4 sentences) is sufficient for high accuracy while keeping the detection overhead under 5ms.

### Multilingual stopwords

NLTK ships with stopword lists for 16+ languages. Once the language is detected, `text_cleaner.remove_stopwords()` uses the appropriate list:

```python
def remove_stopwords(tokens: list, language: str = "english") -> list:
    stop = _get_stopwords(language)   # cached per language
    return [t for t in tokens if t not in stop and len(t) > 1]
```

This means a French document removes French stopwords (`le`, `la`, `de`, `et`) rather than incorrectly using English ones. The stopword lists are cached after first load so repeated calls cost nothing.

### Fallback

If detection fails (very short text, mixed languages, encoding issues), the function silently returns `("en", "english", "English")`. It never raises an exception — the rest of the pipeline is never affected.

---

## 10. Multi-Document Summarization

**Files:** `app/features/summarizer/batch_service.py`, `app/features/file_handler/routes.py`

### Two modes

**Combined mode:**
All document texts are concatenated with double newlines (`\n\n`) into a single string, then passed through the normal single-document summarization pipeline. The result is one summary that covers all documents.

Use case: summarize a collection of related reports into one executive brief.

**Individual mode:**
Each document is summarized independently in a loop. Results are returned as an array — one summary object per document. The UI renders per-document tabs so users can switch between summaries.

Use case: process 5 research papers and compare their individual summaries.

### Batch validation

`BatchSummarizeRequest.from_dict()` validates before any processing starts:
- `documents` must be a non-empty list (max 10)
- Each document: minimum 100 chars, maximum 50,000 chars
- Method, ratio, mode validated same rules as single-document

If document 3 fails validation, the error is returned immediately and none of the documents are processed — fail fast.

### New API endpoints

```
POST /api/upload-multiple
  Input:  multipart/form-data, field "files" (multiple)
  Output: { texts: [...], names: [...], char_counts: [...], errors: [...] }

POST /api/summarize-batch
  Input:  { documents, names, method, ratio, mode }
  Output (combined):    { mode: "combined", document_count, summary, analytics, ... }
  Output (individual):  { mode: "individual", results: [{ doc_name, summary, ... }, ...] }
```

---

## 11. Analytics Module

### Word Frequency (`app/features/analytics/frequency.py`)
```python
from collections import Counter
counts = Counter(flat_tokens)
return [{"word": word, "count": count} for word, count in counts.most_common(15)]
```
Returns the 15 most frequent meaningful words. Used to populate the bar chart.

### Keyword Extraction (`app/features/analytics/keywords.py`)
Uses two strategies:

**Strategy 1 — TF-IDF terms:**
Fits a new TF-IDF vectorizer on token lists and extracts the top feature names (terms with highest TF-IDF weight across the corpus). These are words that are important *and* discriminating.

**Strategy 2 — spaCy noun chunks:**
```python
nlp = spacy.load("en_core_web_sm")
doc = nlp(text)
chunks = [chunk.text for chunk in doc.noun_chunks]
```
spaCy's POS tagger identifies noun phrases (e.g., "machine learning", "global climate change") which tend to be the actual topics of a document, regardless of frequency.

Both lists are merged, deduplicated, and returned as keyword tags displayed in the UI.

### Sentence Scoring (`app/features/analytics/scoring.py`)
Takes the `combined_scores` list from the ranker and adds a human-readable `label`:
- `score >= 0.65` → `"high"` (green border in UI)
- `score >= 0.35` → `"medium"` (amber border)
- `score < 0.35` → `"low"` (grey border)

---

## 12. File Handling

### Upload (`app/features/file_handler/reader.py`)

**Text files:**
```python
with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
    return fh.read()
```
Standard file read with UTF-8 encoding. `errors="replace"` handles files with unusual character encodings gracefully.

**PDF files:**
```python
import pdfplumber
with pdfplumber.open(filepath) as pdf:
    pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
return "\n".join(pages)
```
`pdfplumber` extracts text from each PDF page, handling both scanned-style and text-based PDFs. Pages are joined with newlines to preserve paragraph structure.

**Validation (`app/features/file_handler/validators.py`):**
1. Checks that a file was provided
2. Checks the file extension (.txt or .pdf only)
3. Checks file size ≤ 5 MB

Files are saved temporarily to the `uploads/` directory during processing, then deleted immediately after reading. This means no user data is stored on disk.

### Export (`app/features/file_handler/writer.py`)

**Text export:**
Writes the summary with a header timestamp to a `.txt` file in the `exports/` directory.

**PDF export using reportlab:**
```python
from reportlab.platypus import SimpleDocTemplate, Paragraph
```
`reportlab` is a Python library for generating PDF files programmatically. We create a `SimpleDocTemplate` with A4 page size, define text styles (title, meta, body), and build the document from a list of `Paragraph` and `Spacer` elements. The title uses the project's accent colour (`#7c6aff`).

After the file is sent to the user with `Flask.send_file()`, the file could be cleaned up — in the current implementation they remain in `exports/` for simplicity and can be cleared via `make clean`.

---

## 13. Flask Architecture

### App Factory (`app/__init__.py`)

The `create_app()` pattern is the standard Flask architecture for production applications. Instead of:
```python
app = Flask(__name__)  # module-level global
```

We use:
```python
def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object(config_class or get_config())
    _register_blueprints(app)
    return app
```

**Why?** The factory pattern allows:
- Creating different app instances for testing (with test config) and production (with prod config)
- Avoiding circular imports
- Clean dependency injection

### Blueprints

Flask Blueprints are modular routing containers. Each feature registers its own blueprint:

```python
from flask import Blueprint
summarizer_bp = Blueprint("summarizer", __name__)

@summarizer_bp.route("/api/summarize", methods=["POST"])
def summarize_route():
    ...
```

The main app factory then registers all blueprints:
```python
app.register_blueprint(summarizer_bp)
app.register_blueprint(file_bp)
```

This means routes are defined near their corresponding logic, not in a single monolithic routes file.

### Service Layer

The route functions are thin HTTP adapters:
```python
@summarizer_bp.route("/api/summarize", methods=["POST"])
def summarize_route():
    data = request.get_json()
    req = SummarizeRequest.from_dict(data)  # parse + validate
    response = summarize(req)               # call service
    return jsonify(response.to_dict())      # serialize + return
```

All business logic lives in `service.py`. The route has no knowledge of NLP algorithms, scoring, or analytics. This separation makes each component independently testable.

---

## 14. Validation Layer

Validation happens at two levels:

### Client-side (JavaScript, `main.js`)
Immediate feedback before any network request:
- Empty text → show field error message
- Text < 100 chars → show character count warning
- No file uploaded when file tab active → show toast
- Character count turns yellow at < 100, red at maximum

### Server-side (Python, `schemas.py`)
```python
@classmethod
def from_dict(cls, data: dict) -> "SummarizeRequest":
    text = (data.get("text") or "").strip()
    if len(text) < min_len:
        raise TextTooShortError(f"Text must be at least {min_len} characters.")
    if method not in VALID_METHODS:
        raise ValidationError(f"Method must be one of: {', '.join(VALID_METHODS)}.")
```

Server-side validation is essential because API endpoints can be called directly (bypassing the UI). Custom exception classes (`TextTooShortError`, `ValidationError`, `SummarizationError`) enable precise error responses with appropriate HTTP status codes (422 for validation failures).

---

## 15. Frontend Architecture

The frontend is **server-rendered HTML + Vanilla JavaScript**. No React, no Vue, no build tools.

**Why no framework?**
- Smaller scope: single-page application with one main view
- No npm, no webpack, no compilation step
- Easier to understand and explain
- Loads faster (no 200KB framework bundle)

### How the JS works (`main.js`)

The entire UI logic is wrapped in an IIFE (Immediately Invoked Function Expression):
```javascript
(function () {
  "use strict";
  // all code here
})();
```

This creates a private scope and prevents variable pollution of the global namespace.

**Key flows:**

1. **Text input → character counter** — `textInput.addEventListener("input", ...)` updates the counter on every keystroke.

2. **Tab switching** — Clicking a tab button toggles `tab-content--hidden` CSS class on the relevant panels.

3. **File upload** — `FileReader` and `FormData` are used to send the file to `/api/upload`. The response text is stored in the `uploadedText` variable.

4. **Summarise** — Reads either `textInput.value` or `uploadedText` depending on the active tab, sends a `fetch()` POST to `/api/summarize`, then calls render functions on success.

5. **Results rendering** — `renderKeywords()`, `renderFreqChart()`, `renderScores()` each update specific DOM sections. The chart is rendered by Chart.js via `renderFreqChart()` in `charts.js`.

6. **Export** — `fetch()` POST to `/api/export` returns a binary blob. A hidden `<a>` element is programmatically clicked to trigger a browser download.

---

## 16. Dark / Light Theme System

**How CSS custom properties work:**

```css
[data-theme="dark"] {
  --bg-base: #0f1117;
  --accent:  #7c6aff;
  ...
}

[data-theme="light"] {
  --bg-base: #f4f5fa;
  --accent:  #5b4fe8;
  ...
}

body {
  background-color: var(--bg-base);  /* references the token */
}
```

Switching themes just means changing `document.documentElement.setAttribute("data-theme", "light")`. The browser re-evaluates all `var()` references instantly.

**Persistence:**
```javascript
localStorage.setItem("teyzix-theme", theme);
```
The theme is written to localStorage on every toggle. On page load, `theme.js` reads this value and applies it before the DOM renders, preventing a flash of the wrong theme.

**OS preference fallback:**
```javascript
window.matchMedia("(prefers-color-scheme: light)").matches
```
If no stored preference exists, the system respects the user's OS dark/light preference.

---

## 17. Why NOT LangGraph

LangGraph is a library for building **multi-agent workflows** with complex state machines. It is designed for scenarios like:
- An AI agent that decides to call different tools (web search, database query, calculator) in a dynamic sequence
- A pipeline where the next step depends on the LLM's previous output
- Multi-agent systems where several AI models collaborate

**This project does not need LangGraph because:**

1. The summarisation pipeline is deterministic and linear: preprocess → score → rank → output. There are no conditional branches that require an LLM to decide.

2. The task uses classical NLP (NLTK, spaCy, scikit-learn) — no LLM API calls. LangGraph requires an LLM as its reasoning core.

3. Adding LangGraph would require setting up an LLM API key, add API call latency (1–5 seconds per request), add API costs, and complicate the code significantly.

4. The task specification explicitly asks for NLTK/spaCy approaches.

**When would we use LangGraph?**
If the task required: "Given a document, decide whether to search the web for additional context, then summarise combining both sources, then fact-check against a database" — that's when LangGraph's state machine approach would be appropriate.

---

## 18. How to Run

```bash
# Install everything
make setup

# Start the development server
make run

# Open in browser
http://127.0.0.1:5000

# Run tests
make test
```

### Using the app
1. Paste text in the **Paste Text** tab, or upload a file via **Upload File**
2. Select a **Scoring method** (Combined is recommended)
3. Adjust the **Summary length** slider
4. Click **Summarize**
5. View summary and analytics on the right panel
6. Export as `.txt` or `.pdf` using the export buttons

### Sample documents
Three ready-to-use samples are in `samples/`:
- `climate_report.txt` — 10-paragraph climate science report
- `ai_research.txt` — AI technology overview
- `business_email.txt` — Corporate Q3 review email

---

## 19. Interview Prep

**Q: What is extractive summarisation?**
A: Extractive summarisation selects and returns the most important sentences from the original text without rewriting or paraphrasing. It is contrasted with generative (neural) summarisation which generates new sentences. Extractive is simpler, faster, and guaranteed to produce grammatically correct output since every sentence is taken verbatim.

**Q: What is the difference between extractive and generative summarisation?**
A: Extractive methods (frequency, TF-IDF, combined) score existing sentences and return the highest-scoring ones — output is always copied text from the source. Generative methods (BART) use an encoder-decoder neural network: the encoder reads the full document and produces a vector representation of its meaning, then the decoder generates new tokens one at a time to form a fluent, paraphrased summary. Generative output is higher quality but requires a large model (~1.6 GB) and is much slower (5–30 seconds vs under 1 second).

**Q: What is BART and how does it work?**
A: BART (Bidirectional and Auto-Regressive Transformer) is a sequence-to-sequence neural model from Meta. The encoder reads the entire input simultaneously (bidirectional, like BERT) to build a rich contextual representation. The decoder then generates the summary token-by-token (auto-regressive, like GPT), conditioning each new word on both the encoder output and all previously generated words. The model used is `facebook/bart-large-cnn`, pre-trained on 300,000 news article-summary pairs from CNN and DailyMail.

**Q: How do you handle documents longer than BART's 1024-token limit?**
A: We use hierarchical summarisation. The document is split into 800-word chunks. Each chunk is summarised independently by BART. The resulting chunk summaries are concatenated and passed through BART a second time to produce a single coherent final summary. This preserves information from all parts of the document.

**Q: What is TF-IDF and why is it useful?**
A: TF-IDF (Term Frequency–Inverse Document Frequency) scores words by how frequently they appear in a specific sentence (TF) weighted by how rarely they appear across all sentences (IDF). Words that appear in every sentence score near zero — they are uninformative. Words unique to specific sentences score high — they are distinctive and important. This makes TF-IDF better than raw frequency for identifying the most informative sentences.

**Q: What is the positional bias in the sentence ranker?**
A: Real documents tend to state key information at the beginning (abstract, introduction) and end (conclusion). The ranker adds a 0.1 boost to sentences at positions 0, 1, and the last position to reflect this real-world pattern, improving summary quality for structured documents.

**Q: How does language detection work?**
A: The `langdetect` library samples the first 500 characters of the input and uses a Naive Bayes classifier trained on text profiles for 55 languages. It returns an ISO 639-1 code (e.g., `"fr"` for French). We map this to an NLTK language name and use it to select the appropriate common-word list for that language, so French documents have French common words removed rather than English ones.

**Q: How does multi-document summarisation work?**
A: In combined mode, all document texts are concatenated and passed through the standard single-document pipeline — the result is one summary covering all documents. In individual mode, each document is summarised independently in a loop, and results are returned as an array. The UI shows per-document tabs for switching between individual summaries.

**Q: What is the Flask app factory pattern?**
A: Instead of creating the Flask app at the module level (a global variable), we wrap app creation in a function `create_app()`. This allows creating different app instances with different configurations — useful for testing (test config), development (debug mode on), and production (debug off, strict settings).

**Q: How does the dark/light theme work technically?**
A: CSS custom properties (variables) are defined under `[data-theme="dark"]` and `[data-theme="light"]` selectors on the root HTML element. JavaScript changes the `data-theme` attribute on the `<html>` element, which instantly re-evaluates all CSS variable references. The current choice is persisted to `localStorage` and re-applied on page load.

**Q: How is the file upload handled securely?**
A: Files are validated for extension (.txt/.pdf only) and size (≤ 5MB) before saving. `werkzeug.utils.secure_filename` sanitises the filename to prevent path traversal attacks. Files are saved to a temporary directory, read, and then immediately deleted — no user data is stored on disk.

**Q: Why is BART optional and not always on?**
A: The model file is 1.6 GB and requires approximately 4 GB of RAM to run. It takes 5–30 seconds per document on a CPU. For a demo or presentation this would make the app feel broken. The three extractive methods run in under 1 second with no large downloads. BART is included as a bonus feature for users who have the hardware and patience for higher-quality output.
