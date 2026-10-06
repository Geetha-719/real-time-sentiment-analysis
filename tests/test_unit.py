"""Unit tests for preprocessing, security helpers and dataset cleaning.

Run from the project root:  python -m pytest tests -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from ml.preprocessing import TfidfAnalyzer, preprocess, tokenize  # noqa: E402


# ------------------------- Preprocessing ------------------------- #
def test_lowercasing_and_tokenization():
    assert preprocess("HELLO World", stem=False) == "hello world"


def test_url_mention_hashtag_normalization():
    out = preprocess("Check https://x.com @bob #Great", stem=False)
    assert "url" in out and "user" in out and "great" in out
    assert "@bob" not in out and "https" not in out


def test_negation_preserved():
    # Negations must NOT be removed by stopword handling.
    out = preprocess("this is not good", stem=False)
    assert "not" in out.split()


def test_common_stopwords_removed():
    out = preprocess("the cat and the dog", stem=False)
    assert "the" not in out.split() and "and" not in out.split()
    assert "cat" in out.split()


def test_stemming():
    assert "love" in preprocess("loving loved loves", stem=True).split()


def test_html_stripped():
    assert "<" not in preprocess("<p>hello</p>", stem=False)


def test_empty_and_none():
    assert preprocess("") == ""
    assert preprocess(None) == ""


def test_tokenize_returns_list():
    assert isinstance(tokenize("good bad", stem=False), list)


# ------------------------- TF-IDF analyzer ------------------------- #
def test_analyzer_unigrams():
    a = TfidfAnalyzer(stem=False, ngram_range=(1, 1))
    assert a("good great") == ["good", "great"]


def test_analyzer_bigrams():
    a = TfidfAnalyzer(stem=False, ngram_range=(1, 2))
    grams = a("good great movie")
    assert "good" in grams
    assert "good great" in grams
    assert "great movie" in grams


def test_analyzer_picklable():
    import pickle

    a = TfidfAnalyzer(stem=True, ngram_range=(1, 2))
    restored = pickle.loads(pickle.dumps(a))
    assert restored("good movie") == a("good movie")


# ------------------------- Security ------------------------- #
def test_password_hash_roundtrip():
    from app.security import hash_password, verify_password

    h = hash_password("StrongPass123")
    assert h != "StrongPass123"
    assert verify_password("StrongPass123", h)
    assert not verify_password("WrongPass123", h)


def test_password_hash_unique_salt():
    from app.security import hash_password

    assert hash_password("SamePass123") != hash_password("SamePass123")


def test_long_password_supported():
    from app.security import hash_password, verify_password

    pw = "A" * 200 + "1"
    assert verify_password(pw, hash_password(pw))


def test_jwt_create_decode():
    from app.security import create_access_token, decode_access_token

    token, expires = create_access_token(42)
    assert expires > 0
    payload = decode_access_token(token)
    assert payload["sub"] == "42"


def test_jwt_invalid():
    from app.security import decode_access_token

    assert decode_access_token("not.a.token") is None


def test_reset_token_hash_not_raw():
    from app.security import generate_reset_token, hash_reset_token

    raw, hashed = generate_reset_token()
    assert raw != hashed
    assert hashed == hash_reset_token(raw)


# ------------------------- Dataset cleaning ------------------------- #
def test_clean_removes_missing_duplicates_and_header():
    import pandas as pd
    from ml.training.train import clean
    from ml.config import LABELS

    df = pd.DataFrame(
        {
            "id": ["1", "2", "3", "4", "5", "6"],
            "entity": ["A"] * 6,
            "sentiment": ["Positive", "Positive", "Negative", "Neutral", "Irrelevant", "SENTIMENT"],
            "text": ["good", "good", None, "bad", "  ", "header"],
        }
    )
    out = clean(df)
    # header row removed, missing/empty removed, duplicate "good" collapsed -> 2 rows
    assert len(out) == 2
    assert set(out["sentiment"]).issubset(set(LABELS))
    assert out["text"].str.strip().ne("").all()
    assert out["text"].duplicated().sum() == 0


# ------------------------- Inference (requires trained model) ------------------------- #
@pytest.mark.skipif(
    not (ROOT / "ml" / "models" / "sentiment_model.joblib").exists(),
    reason="trained model not present",
)
def test_prediction_positive_negative():
    from ml.inference import predict

    pos = predict("I absolutely love this, it is amazing and works perfectly!")
    neg = predict("This is the worst experience ever, terrible service and broken item.")
    assert pos["prediction"] == "Positive"
    assert neg["prediction"] == "Negative"
    assert 0 <= pos["confidence"] <= 1


@pytest.mark.skipif(
    not (ROOT / "ml" / "models" / "sentiment_model.joblib").exists(),
    reason="trained model not present",
)
def test_prediction_explanation_is_derived():
    from ml.inference import predict

    a = predict("I absolutely love this amazing product")
    b = predict("This terrible awful product is the worst")
    # Explanations must differ between contrasting inputs.
    assert a["simple_explanation"] != b["simple_explanation"]


@pytest.mark.skipif(
    not (ROOT / "ml" / "models" / "sentiment_model.joblib").exists(),
    reason="trained model not present",
)
def test_prediction_empty_raises():
    from ml.inference import predict

    with pytest.raises(ValueError):
        predict("   ")
