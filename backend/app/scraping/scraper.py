"""Real web scraping: fetch a user-provided URL and extract its text.

Flow:
    URL -> requests.get() -> HTML -> BeautifulSoup -> extracted text

Safety / robustness:
* Only http/https URLs are accepted.
* Private / local hosts are rejected (SSRF protection).
* robots.txt is respected for the target host.
* Clear errors for invalid URLs, timeouts, connection failures, HTTP errors,
  empty pages and pages with too little text.
* A descriptive User-Agent is sent. No CAPTCHA/login/paywall bypass.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from app.scraping.extractor import extract_text_from_html, extract_title_from_html

USER_AGENT = (
    "Mozilla/5.0 (compatible; SentimentScraper/1.0; "
    "+academic-project; respects robots.txt)"
)
REQUEST_TIMEOUT = 15          # seconds
MAX_CONTENT_BYTES = 5_000_000  # 5 MB cap to avoid huge downloads
MIN_TEXT_CHARS = 40           # below this we consider the page "too little text"

# Only these schemes are allowed.
ALLOWED_SCHEMES = {"http", "https"}


class ScrapeError(Exception):
    """User-presentable scraping error with a machine-readable kind."""

    def __init__(self, message: str, *, kind: str = "error", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.kind = kind
        self.status_code = status_code


@dataclass
class ScrapedPage:
    url: str
    final_url: str
    title: str
    text: str
    word_count: int
    content_type: str = ""
    status_code: int = 200
    warnings: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# URL validation & safety
# --------------------------------------------------------------------------- #
def normalize_url(url: str) -> str:
    """Validate and normalize a user-supplied URL. Raises ScrapeError if invalid."""
    if not url or not str(url).strip():
        raise ScrapeError("Please enter a webpage URL.", kind="invalid_url")
    url = str(url).strip()
    if not url.startswith(("http://", "https://")):
        # Be forgiving if the user typed "example.com" without a scheme.
        url = "https://" + url

    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ScrapeError("Only http:// and https:// URLs are supported.", kind="invalid_url")
    if not parsed.netloc:
        raise ScrapeError("That URL looks invalid. Please check it and try again.", kind="invalid_url")

    host = parsed.hostname or ""
    if not host or "." not in host:
        raise ScrapeError("That URL looks invalid. Please check it and try again.", kind="invalid_url")

    _reject_private_host(host)
    return url


def _reject_private_host(host: str) -> None:
    """Block localhost / private IPs to avoid SSRF against internal services."""
    if host.lower() in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
        raise ScrapeError("Local and private addresses cannot be analyzed.", kind="blocked")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        # Cannot resolve -> will fail later with a friendly connection error.
        return
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ScrapeError("Local and private addresses cannot be analyzed.", kind="blocked")


def robots_allows(url: str, user_agent: str = USER_AGENT) -> bool:
    """Return True if robots.txt permits fetching this URL.

    If robots.txt cannot be read, we are permissive (most public pages do not
    publish one), but we never bypass auth/paywalls/CAPTCHAs regardless.
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True


# --------------------------------------------------------------------------- #
# Main scraper
# --------------------------------------------------------------------------- #
def scrape_url(url: str, *, respect_robots: bool = True) -> ScrapedPage:
    """Download a webpage and extract its meaningful text.

    Raises ScrapeError with a friendly message on any failure.
    """
    url = normalize_url(url)

    if respect_robots and not robots_allows(url):
        raise ScrapeError(
            "This website's robots.txt does not allow automated access.",
            kind="robots_blocked", status_code=403,
        )

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    except requests.exceptions.SSLError:
        raise ScrapeError("Could not establish a secure connection to that website.", kind="connection")
    except requests.exceptions.Timeout:
        raise ScrapeError("The webpage took too long to respond. Please try again.", kind="timeout", status_code=504)
    except requests.exceptions.ConnectionError:
        raise ScrapeError("Could not reach that webpage. Please check the URL or your connection.", kind="connection")
    except requests.exceptions.InvalidURL:
        raise ScrapeError("That URL looks invalid. Please check it and try again.", kind="invalid_url")
    except requests.exceptions.RequestException:
        raise ScrapeError("The webpage could not be downloaded right now.", kind="connection")

    if resp.status_code == 404:
        raise ScrapeError("The webpage was not found (HTTP 404).", kind="http_error", status_code=404)
    if resp.status_code in (401, 403):
        raise ScrapeError(
            "This webpage blocked the request (HTTP 401/403). It may require login or block bots.",
            kind="http_error", status_code=403,
        )
    if resp.status_code == 429:
        raise ScrapeError("The website is rate-limiting requests. Please try again later.", kind="rate_limited", status_code=429)
    if resp.status_code >= 400:
        raise ScrapeError(f"The webpage returned an error (HTTP {resp.status_code}).", kind="http_error")

    content_type = resp.headers.get("Content-Type", "")
    if content_type and "html" not in content_type.lower() and "xml" not in content_type.lower():
        raise ScrapeError(
            f"That URL is not an HTML webpage (content type: {content_type.split(';')[0]}).",
            kind="not_html",
        )

    # Guard against very large pages.
    if resp.content and len(resp.content) > MAX_CONTENT_BYTES:
        raise ScrapeError("That webpage is too large to analyze.", kind="too_large")

    html = resp.text
    if not html or not html.strip():
        raise ScrapeError("The webpage returned no content.", kind="empty")

    title = extract_title_from_html(html)
    text = extract_text_from_html(html)
    word_count = len(text.split())

    if len(text) < MIN_TEXT_CHARS:
        raise ScrapeError(
            "This page did not contain enough readable text to analyze. "
            "It may rely on JavaScript or be mostly images/video.",
            kind="too_little_text",
        )

    return ScrapedPage(
        url=url,
        final_url=resp.url,
        title=title or url,
        text=text,
        word_count=word_count,
        content_type=content_type.split(";")[0] if content_type else "",
        status_code=resp.status_code,
    )
