# Real-Time Sentiment Analysis Using Web Scraping

A college-level Machine Learning project that takes a **webpage URL**, scrapes its text with
`requests` + **BeautifulSoup**, and predicts the page's sentiment with a **TF-IDF + Logistic
Regression** model trained on labelled data.

```
USER ENTERS A URL
      ↓
BACKEND FETCHES THE PAGE        (requests.get)
      ↓
SCRAPER EXTRACTS TEXT           (BeautifulSoup)
      ↓
TEXT CLEANING / NLP PREPROCESSING
      ↓
TF-IDF  (saved vectorizer)
      ↓
TRAINED ML MODEL (Logistic Regression)
      ↓
SENTIMENT PREDICTION
      ↓
WEB INTERFACE SHOWS THE RESULT
```

---

## 1. Problem Statement

Understanding the sentiment of online content usually means reading pages manually — slow and
impossible at scale. This project automates that: give it a publicly accessible webpage URL and it
will fetch the page, extract the readable text, and classify the sentiment as **Positive**,
**Negative**, **Neutral** or **Irrelevant**, showing an overall result, a confidence value and a
distribution across the page.

## 2. Objectives

1. Implement **real web scraping** (HTTP request → HTML → BeautifulSoup → text).
2. Extract only meaningful page text (remove scripts, styles, nav, footers).
3. Apply the **same NLP preprocessing** used during training.
4. Use a **saved TF-IDF** vectorizer (never re-fitted on scraped text).
5. Predict sentiment with a **trained Logistic Regression** model.
6. Aggregate chunk predictions into an overall page sentiment + distribution.
7. Provide a clean, responsive web app with history and a dashboard.
8. Report **honest** metrics and limitations.

## 3. Technologies Used

| Area | Technology |
|---|---|
| Language | Python 3.11+ (tested on 3.14) |
| Web scraping | `requests`, `BeautifulSoup4` (bs4) |
| Machine learning | `scikit-learn` (TF-IDF, Logistic Regression, Multinomial Naive Bayes) |
| NLP | `nltk` (Porter stemmer), custom preprocessing |
| Backend | FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL |
| Auth | JWT (PyJWT), bcrypt password hashing |
| Frontend | React + Vite, Tailwind CSS, Recharts, Axios |

> Deliberately **no** Kafka, Spark, Hadoop, LSTM or Transformers — this keeps the project simple and
> correct for a student demonstration.

## 4. System Architecture

```
┌──────────────┐   POST /api/analyze-url   ┌──────────────────────────────────┐
│  React app   │ ────────────────────────▶ │            FastAPI                │
│ (URL input)  │ ◀──────────────────────── │  routes/analyze.py                │
└──────────────┘   sentiment + charts      │      ↓                            │
                                           │  services/scraping_service.py     │
                                           │      ↓                            │
                                           │  scraping/scraper.py  (requests)  │
                                           │  scraping/extractor.py (bs4)      │
                                           │      ↓                            │
                                           │  ml_service → ml/inference.py     │
                                           │  (saved TF-IDF + LogReg pipeline) │
                                           └──────────────┬───────────────────┘
                                                          │ SQLAlchemy
                                                   ┌──────▼──────┐
                                                   │ PostgreSQL  │
                                                   │url_analyses │
                                                   └─────────────┘
```

## 5. Dataset

Two labelled Twitter sentiment CSV files in `data/raw/` (columns `ID, ENTITY, SENTIMENT, TWEET`).
The `TWEET` column is the text input and `SENTIMENT` is the target.

- **Classes (4):** Negative, Neutral, Positive, Irrelevant.
- **Raw rows:** 75,683 across both files.
- **After cleaning:** 69,971 rows (removed missing/empty text and duplicate texts).

Cleaning is reproducible in `ml/training/train.py` (`clean()`): drops rows with the header line,
null/empty text and duplicate texts.

## 6. NLP Preprocessing

`ml/preprocessing/__init__.py` — used **identically** at training and prediction time:

- unescape HTML entities, strip HTML tags, repair mojibake;
- lowercase;
- replace URLs with `url`, mentions with `user`, split hashtags;
- remove emojis/symbols, tokenize `[a-z0-9]+(?:'[a-z]+)?`;
- remove a **conservative** stopword list (negations like *not* are kept);
- optional Porter stemming.

## 7. TF-IDF

A single scikit-learn `Pipeline` holds the vectorizer and the classifier:

```python
Pipeline([
    ("tfidf", TfidfVectorizer(analyzer=TfidfAnalyzer(...), ngram_range=(1,2))),
    ("clf",   LogisticRegression(...)),
])
```

The vectorizer is **fitted only on the training split** and saved inside the pipeline with `joblib`.
At prediction time the scraped text is **transformed** by the saved vectorizer — it is never re-fitted.

## 8. Machine Learning Model

`ml/training/train.py` compares **Multinomial Naive Bayes** and **Logistic Regression** across
unigram / unigram+bigram and stemming configurations by cross-validation, picks the best by macro F1,
and saves the winner to `ml/models/sentiment_model.joblib` along with `metadata.json` and
`metrics.json`.

## 9. Web Scraping

`backend/app/scraping/`:

- **`scraper.py` → `scrape_url(url)`** — validates the URL (http/https only, blocks localhost/private
  IPs), checks `robots.txt`, sends `requests.get()` with a descriptive User-Agent and timeout,
  handles HTTP/connection/timeout errors, then calls the extractor.
- **`extractor.py` → `extract_text_from_html(html)` / `extract_title_from_html(html)`** — parse HTML
  with BeautifulSoup, remove `script/style/noscript/nav/footer/header/aside/form/...`, prefer
  `<article>`/`<main>`, and return clean, whitespace-normalised text.
- **`cleaner.py`** — removes boilerplate and splits text into short chunks.

No CAPTCHA, login, paywall or anti-bot bypass is attempted. Only publicly accessible pages are used.

## 10. Real-Time URL Analysis

`backend/app/services/scraping_service.py → analyze_url(url)`:

1. Scrape the page (title + text).
2. Clean text and split into short chunks (~400 chars, ≥4 words).
3. Run each chunk through the saved ML pipeline (`predict_batch`).
4. Aggregate: percentage distribution per class; overall = most frequent class; confidence = mean
   model probability for that class.
5. Add a note for factual/informational pages.

Example response:

```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "overall_sentiment": "Neutral",
  "confidence": 0.87,
  "word_count": 542,
  "chunks_analyzed": 12,
  "sentiment_distribution": {"Positive": 8, "Negative": 8, "Neutral": 76, "Irrelevant": 8},
  "preview": "This domain is for use in documentation examples ..."
}
```

## 11. Web Application

- **Analyze URL** page — the main workflow: URL input, loading state, result card (title, overall
  sentiment, confidence, words analyzed, distribution bars, text preview, analyzed URL) and an
  “Analyze Another URL” button.
- **Dashboard** — total webpages analyzed, positive/negative/neutral counts, 14-day trend,
  distribution bar chart and recent analyses.
- **History** — paginated list of analyzed URLs with search, sentiment filter, view and delete.
- **Model Insights** — real accuracy/precision/recall/F1, confusion matrices and top terms.
- **How It Works** — plain-language explanation of the pipeline.
- Auth (register/login/logout/forgot & reset password), dark/light mode, responsive layout.

## 12. Model Evaluation

Actual results on the held-out test set (13,995 samples):

| Model | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) | F1 (weighted) |
|---|---|---|---|---|---|
| Naive Bayes | 92.26% | 93.13% | 91.56% | 92.19% | 92.26% |
| **Logistic Regression** | **93.11%** | **93.44%** | **92.73%** | **93.05%** | **93.11%** |

Chosen model: **Logistic Regression**, unigram+bigram, no stemming. Full report: run
`python -m ml.evaluation.report` (writes `reports/model_report.md`).

## 13. How to Run

### Prerequisites
- Python 3.11+, Node 18+, PostgreSQL 14+.

### Backend
```bash
cd backend
pip install -r requirements.txt

# create backend/.env from the template and set DATABASE_URL + JWT_SECRET
copy .env.example .env            # Windows
# cp .env.example .env            # Unix

# create database + run migrations
python scripts/init_db.py
set PYTHONPATH=backend            # Windows (Unix: export PYTHONPATH=backend)
python -m alembic -c backend/alembic.ini upgrade head

# train the model (once)
python -m ml.training.train

# run the API
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /api to :8000)
```

## 14. Example Usage

1. Open http://localhost:5173 and sign up.
2. Go to **Analyze URL**.
3. Paste a public page, e.g. `https://en.wikipedia.org/wiki/Sentiment_analysis` or `https://example.com`.
4. Click **Analyze Sentiment**.
5. See the title, overall sentiment, confidence, distribution, word count and text preview.

## 15. Tests

```bash
python -m pytest tests/test_unit.py tests/test_scraping.py -q   # unit + scraper (mocked, no internet)
python tests/test_api.py                                        # end-to-end (backend must be running)
```

Scraper tests use mocking so they never depend on live websites.

## 16. Limitations

- Works only on **publicly accessible** pages. Some websites block automated requests (handled with a
  clear message) — we do not bypass them.
- JavaScript-rendered pages may expose little readable HTML text.
- The model was trained on short social-media-style texts; chunking is used to reduce mismatch, but
  very long or specialised articles may be less accurate.
- Factual/informational pages usually score **Neutral** — this is expected.
- Sarcasm and mixed opinions remain difficult for classical models.

## 17. Future Enhancements

- JavaScript rendering fallback (e.g. a headless browser) for dynamic pages.
- Transformer-based model (e.g. DistilBERT) for higher accuracy.
- Aspect-based sentiment (per-topic sentiment within a page).
- Export analysis reports as PDF/CSV.

---

*Honest note: this project performs real scraping and real ML prediction. It does not use fake data,
hardcoded results, streaming, or the Twitter/news APIs.*
