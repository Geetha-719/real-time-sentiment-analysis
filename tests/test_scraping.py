"""Tests for real web scraping (mocked HTTP; no live websites required).

Run from the project root:  python -m pytest tests -q
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.scraping.extractor import extract_text_from_html, extract_title_from_html  # noqa: E402
from app.scraping.scraper import ScrapeError, normalize_url, scrape_url  # noqa: E402
from app.scraping.cleaner import clean_scraped_text, split_into_chunks  # noqa: E402


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Acme Laptops — Review</title>
  <meta property="og:title" content="Acme Laptop Review 2026" />
  <style>.x{color:red}</style>
  <script>console.log("tracking")</script>
</head>
<body>
  <nav><a href="/">Home</a><a href="/about">About</a></nav>
  <header><h1>Top navigation</h1></header>
  <article>
    <h1>Acme Laptop Review 2026</h1>
    <p>I absolutely love this laptop. The battery is fantastic and the screen is beautiful.</p>
    <p>However, the keyboard feels cheap and the fan is noisy. Still, overall I am happy with it.</p>
  </article>
  <footer>© 2026 Acme. All rights reserved.</footer>
  <noscript>Enable JavaScript</noscript>
</body>
</html>
"""


# ------------------------- Text extraction ------------------------- #
def test_extract_title_prefers_og_title():
    assert extract_title_from_html(SAMPLE_HTML) == "Acme Laptop Review 2026"


def test_extract_title_from_plain_title():
    html = "<html><head><title>Hello World</title></head><body>x</body></html>"
    assert extract_title_from_html(html) == "Hello World"


def test_extract_text_removes_script_style_nav_footer():
    text = extract_text_from_html(SAMPLE_HTML)
    assert "console.log" not in text
    assert "color:red" not in text
    assert "Home" not in text          # nav removed
    assert "All rights reserved" not in text  # footer removed
    assert "Enable JavaScript" not in text    # noscript removed
    assert "absolutely love this laptop" in text
    assert "keyboard feels cheap" in text


def test_extract_text_empty():
    assert extract_text_from_html("") == ""


# ------------------------- URL validation ------------------------- #
def test_normalize_url_adds_scheme():
    assert normalize_url("example.com/page").startswith("https://")


def test_normalize_url_rejects_empty():
    with pytest.raises(ScrapeError):
        normalize_url("")


def test_normalize_url_rejects_bad_scheme():
    with pytest.raises(ScrapeError):
        normalize_url("ftp://example.com/file")


def test_normalize_url_rejects_localhost():
    with pytest.raises(ScrapeError):
        normalize_url("http://localhost:8000/admin")


# ------------------------- Scraper (mocked HTTP) ------------------------- #
def _mock_response(html: str, status: int = 200, url: str = "https://example.com/article"):
    resp = Mock()
    resp.status_code = status
    resp.text = html
    resp.content = html.encode("utf-8")
    resp.url = url
    resp.headers = {"Content-Type": "text/html; charset=utf-8"}
    return resp


def test_scrape_url_success(monkeypatch):
    monkeypatch.setattr("app.scraping.scraper.robots_allows", lambda *a, **k: True)
    with patch("app.scraping.scraper.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        page = scrape_url("https://example.com/article")
    assert page.title == "Acme Laptop Review 2026"
    assert page.word_count > 10
    assert "battery is fantastic" in page.text


def test_scrape_url_http_404(monkeypatch):
    monkeypatch.setattr("app.scraping.scraper.robots_allows", lambda *a, **k: True)
    with patch("app.scraping.scraper.requests.get", return_value=_mock_response("", status=404)):
        with pytest.raises(ScrapeError) as exc:
            scrape_url("https://example.com/missing")
    assert exc.value.kind == "http_error"


def test_scrape_url_timeout(monkeypatch):
    monkeypatch.setattr("app.scraping.scraper.robots_allows", lambda *a, **k: True)
    with patch("app.scraping.scraper.requests.get", side_effect=requests.exceptions.Timeout):
        with pytest.raises(ScrapeError) as exc:
            scrape_url("https://example.com/slow")
    assert exc.value.kind == "timeout"


def test_scrape_url_connection_error(monkeypatch):
    monkeypatch.setattr("app.scraping.scraper.robots_allows", lambda *a, **k: True)
    with patch("app.scraping.scraper.requests.get", side_effect=requests.exceptions.ConnectionError):
        with pytest.raises(ScrapeError) as exc:
            scrape_url("https://nonexistent.invalid/x")
    assert exc.value.kind == "connection"


def test_scrape_url_empty_page(monkeypatch):
    monkeypatch.setattr("app.scraping.scraper.robots_allows", lambda *a, **k: True)
    with patch("app.scraping.scraper.requests.get", return_value=_mock_response("")):
        with pytest.raises(ScrapeError) as exc:
            scrape_url("https://example.com/empty")
    assert exc.value.kind == "empty"


def test_scrape_url_too_little_text(monkeypatch):
    monkeypatch.setattr("app.scraping.scraper.robots_allows", lambda *a, **k: True)
    html = "<html><body><p>Hi</p></body></html>"
    with patch("app.scraping.scraper.requests.get", return_value=_mock_response(html)):
        with pytest.raises(ScrapeError) as exc:
            scrape_url("https://example.com/tiny")
    assert exc.value.kind == "too_little_text"


def test_scrape_url_blocks_non_html(monkeypatch):
    monkeypatch.setattr("app.scraping.scraper.robots_allows", lambda *a, **k: True)
    resp = _mock_response("PDFDATA")
    resp.headers = {"Content-Type": "application/pdf"}
    with patch("app.scraping.scraper.requests.get", return_value=resp):
        with pytest.raises(ScrapeError) as exc:
            scrape_url("https://example.com/file.pdf")
    assert exc.value.kind == "not_html"


def test_scrape_respects_robots(monkeypatch):
    monkeypatch.setattr("app.scraping.scraper.robots_allows", lambda *a, **k: False)
    with pytest.raises(ScrapeError) as exc:
        scrape_url("https://example.com/blocked")
    assert exc.value.kind == "robots_blocked"


# ------------------------- Cleaning & chunking ------------------------- #
def test_clean_scraped_text_removes_boilerplate():
    text = "Great article here.\nRead more\nAll rights reserved"
    cleaned = clean_scraped_text(text)
    assert "Read more" not in cleaned
    assert "All rights reserved" not in cleaned
    assert "Great article here." in cleaned


def test_split_into_chunks():
    text = (
        "I love this product and it works great. "
        "The delivery was fast and the support team was helpful. "
        "However the packaging was damaged on arrival."
    )
    chunks = split_into_chunks(text, max_chars=60)
    assert len(chunks) >= 2
    assert all(len(c.split()) >= 4 for c in chunks)
