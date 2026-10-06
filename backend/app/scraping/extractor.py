"""HTML text extraction using BeautifulSoup.

These functions are called by the scraper (``app.scraping.scraper``) after an
HTTP response has been downloaded. They are real, used code — not scaffolding.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

# Elements that never contain meaningful page text for sentiment analysis.
REMOVE_TAGS = (
    "script",
    "style",
    "noscript",
    "template",
    "svg",
    "iframe",
    "form",
    "nav",
    "footer",
    "header",
    "aside",
    "button",
    "input",
    "select",
    "textarea",
)

# Block-level tags used to separate text into readable lines.
BLOCK_TAGS = (
    "p",
    "div",
    "section",
    "article",
    "main",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "ul",
    "ol",
    "tr",
    "td",
    "th",
    "blockquote",
    "figure",
    "figcaption",
)

_WS_RE = re.compile(r"[ \t\r\f\v]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{2,}")


def make_soup(html: str) -> BeautifulSoup:
    """Parse HTML with the built-in parser (no external C dependency)."""
    return BeautifulSoup(html or "", "html.parser")


def extract_title_from_html(html: str) -> str:
    """Best-effort page title: og:title -> twitter:title -> <title> -> <h1>."""
    soup = make_soup(html)
    for attrs in (
        {"property": "og:title"},
        {"name": "twitter:title"},
        {"name": "title"},
    ):
        meta = soup.find("meta", attrs=attrs)
        if meta and meta.get("content"):
            content = _WS_RE.sub(" ", meta["content"]).strip()
            if content:
                return content
    if soup.title and soup.title.string:
        title = _WS_RE.sub(" ", soup.title.string).strip()
        if title:
            return title
    h1 = soup.find("h1")
    if h1:
        return _WS_RE.sub(" ", h1.get_text(" ", strip=True)).strip()
    return ""


def extract_text_from_html(html: str) -> str:
    """Extract visible, meaningful text from an HTML document.

    Removes scripts/styles/nav/footer/etc., keeps paragraph structure, and
    collapses excessive whitespace. Returns a newline-separated string.
    """
    if not html:
        return ""
    soup = make_soup(html)

    for tag in soup.find_all(REMOVE_TAGS):
        tag.decompose()

    # Prefer the main content region when the page marks one.
    container = soup.find("article") or soup.find("main") or soup.body or soup

    for br in container.find_all(["br", "hr"]):
        br.replace_with("\n")
    for block in container.find_all(BLOCK_TAGS):
        block.append("\n")

    raw = container.get_text("\n")
    lines: list[str] = []
    for line in raw.split("\n"):
        line = _WS_RE.sub(" ", line).strip()
        if len(line) > 1:
            lines.append(line)

    text = "\n".join(lines)
    text = _MULTI_NEWLINE_RE.sub("\n", text)
    return text.strip()
