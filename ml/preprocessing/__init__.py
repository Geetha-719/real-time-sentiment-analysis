"""Reusable, leak-free text preprocessing.

The SAME `preprocess` function is used at training time and at prediction
time. It is implemented as a pure-python callable (not an sklearn transformer)
so a plain TF-IDF `analyzer` can call it directly.

Pipeline
--------
1. Unescape HTML entities and strip HTML tags.
2. Lowercase.
3. Replace URLs, @mentions and #hashtags with neutral placeholders.
4. Remove emojis / non-text symbols but keep letters, digits and basic
   punctuation used for abbreviation.
5. Tokenize on word boundaries.
6. Remove conservative stopwords (negations are preserved).
7. Porter-stem each token (configurable).

Stemming vs. no stemming is compared during training via cross-validation.
"""
from __future__ import annotations

import html
import re
import unicodedata

from nltk.stem import PorterStemmer

from ml.config import STOPWORDS

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_MENTION_RE = re.compile(r"@\w+")
_HASHTAG_RE = re.compile(r"#(\w+)")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")

_stemmer = PorterStemmer()

# Cache stemmed tokens to keep large batch processing fast.
_stem_cache: dict[str, str] = {}


def _stem(token: str) -> str:
    cached = _stem_cache.get(token)
    if cached is not None:
        return cached
    result = _stemmer.stem(token)
    _stem_cache[token] = result
    return result


def clean_raw_text(text: str) -> str:
    """Structural clean-up applied before tokenization."""
    if text is None:
        return ""
    text = str(text)
    # Repair mojibake commonly found in scraped tweets, e.g. "�?T" -> "'"
    text = (
        text.replace("\u2019", "'").replace("\u2018", "'")
        .replace("\u201c", '"').replace("\u201d", '"')
        .replace("\ufffd", " ")
    )
    text = html.unescape(text)
    text = _HTML_TAG_RE.sub(" ", text)
    text = _URL_RE.sub(" url ", text)
    text = _MENTION_RE.sub(" user ", text)
    text = _HASHTAG_RE.sub(r" \1 ", text)
    # Normalize unicode; drop emoji/control chars but keep ascii letters/digits.
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    return text


def preprocess(text: str, *, stem: bool = True, remove_stopwords: bool = True) -> str:
    """Return a normalized, space-joined token string ready for TF-IDF."""
    text = clean_raw_text(text)
    tokens = _TOKEN_RE.findall(text)
    out: list[str] = []
    for tok in tokens:
        if remove_stopwords and tok in STOPWORDS:
            continue
        if len(tok) == 1 and tok not in {"a", "i"}:
            # Drop isolated single characters produced by symbol noise.
            continue
        out.append(_stem(tok) if stem else tok)
    return " ".join(out)


def tokenize(text: str, *, stem: bool = True, remove_stopwords: bool = True) -> list[str]:
    """Token list variant (used by the LSTM vectorizer)."""
    processed = preprocess(text, stem=stem, remove_stopwords=remove_stopwords)
    return processed.split() if processed else []


class TfidfAnalyzer:
    """Picklable callable analyzer for sklearn's TfidfVectorizer.

    A *module-level class* (not a closure) is required so the fitted vectorizer
    can be serialized with joblib and reloaded by the API. Because a callable
    analyzer bypasses sklearn's own n-gram logic, n-grams are generated here.
    """

    def __init__(self, stem: bool = True, ngram_range: tuple[int, int] = (1, 1)):
        self.stem = stem
        self.ngram_range = tuple(ngram_range)

    def __call__(self, text: str) -> list[str]:
        tokens = preprocess(text, stem=self.stem).split()
        if not tokens:
            return []
        min_n, max_n = self.ngram_range
        if min_n == 1 and max_n == 1:
            return tokens
        grams: list[str] = []
        for n in range(min_n, max_n + 1):
            if n == 1:
                grams.extend(tokens)
            else:
                grams.extend(" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1))
        return grams

    def __reduce__(self):
        return (TfidfAnalyzer, (self.stem, self.ngram_range))
