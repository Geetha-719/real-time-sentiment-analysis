"""End-to-end API tests against a running backend.

Usage:
    python tests/test_api.py            # requires backend on http://127.0.0.1:8000
Exits non-zero on any failure.
"""
from __future__ import annotations

import sys
import time
import uuid

import requests

BASE = "http://127.0.0.1:8000/api"
PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = ""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED += 1
        FAILURES.append(name)
        print(f"  FAIL  {name} {detail}")


def wait_for_server(timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{BASE}/health", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1.5)
    return False


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    if not wait_for_server():
        print("Server did not become ready.")
        return 1

    print("\n=== HEALTH ===")
    r = requests.get(f"{BASE}/health")
    check("health 200", r.status_code == 200, r.text)
    check("model_ready", r.json().get("model_ready") is True, r.text)

    suffix = uuid.uuid4().hex[:8]
    email = f"alice_{suffix}@Example.COM"
    password = "StrongPass123"

    print("\n=== AUTH ===")
    r = requests.post(
        f"{BASE}/auth/register",
        json={"full_name": "Alice Tester", "email": email, "password": password, "confirm_password": password},
    )
    check("register 201", r.status_code == 201, r.text)
    token_a = r.json().get("access_token") if r.status_code == 201 else None

    r = requests.post(
        f"{BASE}/auth/register",
        json={"full_name": "Alice Clone", "email": email.lower(), "password": password, "confirm_password": password},
    )
    check("duplicate email 409", r.status_code == 409, r.text)

    r = requests.post(f"{BASE}/auth/login", json={"email": email.upper(), "password": password})
    check("login normalized email", r.status_code == 200, r.text)
    token_a = r.json().get("access_token") if r.status_code == 200 else token_a

    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": "WrongPass123"})
    check("wrong password 401", r.status_code == 401, r.text)

    r = requests.get(f"{BASE}/auth/me", headers=auth_header(token_a))
    check("me 200", r.status_code == 200, r.text)

    print("\n=== ANALYZE-URL: validation & errors ===")
    r = requests.post(f"{BASE}/analyze-url", json={"url": "not a url"}, headers=auth_header(token_a))
    check("invalid url error", r.status_code in (400, 422), r.text)

    r = requests.post(f"{BASE}/analyze-url", json={"url": ""}, headers=auth_header(token_a))
    check("empty url rejected", r.status_code == 422, r.text)

    r = requests.post(f"{BASE}/analyze-url", json={"url": "http://localhost:8000/x"}, headers=auth_header(token_a))
    check("localhost blocked", r.status_code in (400, 403), r.text)

    r = requests.post(
        f"{BASE}/analyze-url",
        json={"url": "https://nonexistent-domain-xyz-123.invalid/page"},
        headers=auth_header(token_a),
    )
    check("unreachable url handled gracefully", r.status_code in (400, 502, 504), r.text)

    r = requests.post(f"{BASE}/analyze-url", json={"url": "https://example.com"})
    check("unauthenticated analyze-url blocked", r.status_code in (401, 403), r.text)

    print("\n=== ANALYZE-URL: real scraping (example.com) ===")
    r = requests.post(f"{BASE}/analyze-url", json={"url": "https://example.com"}, headers=auth_header(token_a), timeout=60)
    check("analyze example.com 200", r.status_code == 200, r.text)
    analysis_id = None
    if r.status_code == 200:
        body = r.json()
        analysis_id = body["id"]
        check("has title", bool(body["title"]), r.text)
        check("has overall_sentiment", body["overall_sentiment"] in {"Positive", "Negative", "Neutral", "Irrelevant"}, r.text)
        check("confidence in range", 0 <= body["confidence"] <= 1, r.text)
        check("word_count > 0", body["word_count"] > 0, r.text)
        check("distribution present", set(body["sentiment_distribution"]).issuperset({"Positive", "Negative", "Neutral", "Irrelevant"}), r.text)
        check("preview present", bool(body["preview"]), r.text)

    print("\n=== URL HISTORY ===")
    r = requests.get(f"{BASE}/url-history", headers=auth_header(token_a))
    check("history 200", r.status_code == 200, r.text)
    check("history has records", r.json()["total"] >= 1, r.text)

    r = requests.get(f"{BASE}/url-history", params={"sentiment": "Neutral"}, headers=auth_header(token_a))
    check("history filter", r.status_code == 200 and all(i["overall_sentiment"] == "Neutral" for i in r.json()["items"]), r.text)

    r = requests.get(f"{BASE}/url-history", params={"search": "example"}, headers=auth_header(token_a))
    check("history search", r.status_code == 200, r.text)

    print("\n=== USER ISOLATION ===")
    email_b = f"bob_{suffix}@example.com"
    rb = requests.post(
        f"{BASE}/auth/register",
        json={"full_name": "Bob Other", "email": email_b, "password": password, "confirm_password": password},
    )
    token_b = rb.json().get("access_token")
    check("second user registered", rb.status_code == 201, rb.text)

    r = requests.get(f"{BASE}/url-history", headers=auth_header(token_b))
    check("user B sees no user A history", r.json()["total"] == 0, r.text)

    if analysis_id:
        r = requests.get(f"{BASE}/url-history/{analysis_id}", headers=auth_header(token_b))
        check("user B cannot read user A analysis 404", r.status_code == 404, r.text)
        r = requests.delete(f"{BASE}/url-history/{analysis_id}", headers=auth_header(token_b))
        check("user B cannot delete user A analysis 404", r.status_code == 404, r.text)

    print("\n=== DASHBOARD / PROFILE / MODEL ===")
    r = requests.get(f"{BASE}/dashboard", headers=auth_header(token_a))
    check("dashboard 200", r.status_code == 200, r.text)
    d = r.json()
    check("dashboard total", d["total_analyses"] >= 1, r.text)
    check("dashboard total_words", isinstance(d["total_words"], int), r.text)

    r = requests.get(f"{BASE}/profile", headers=auth_header(token_a))
    check("profile 200", r.status_code == 200, r.text)

    r = requests.get(f"{BASE}/model-performance", headers=auth_header(token_a))
    check("model-performance 200", r.status_code == 200, r.text)
    check("model metrics present", r.json()["available"] and len(r.json()["models"]) >= 2, r.text)

    print("\n=== DELETE own analysis ===")
    if analysis_id:
        r = requests.delete(f"{BASE}/url-history/{analysis_id}", headers=auth_header(token_a))
        check("delete own analysis 200", r.status_code == 200, r.text)
        r = requests.get(f"{BASE}/url-history/{analysis_id}", headers=auth_header(token_a))
        check("deleted analysis 404", r.status_code == 404, r.text)

    print(f"\n{'='*50}\nRESULT: {PASSED} passed, {FAILED} failed")
    if FAILURES:
        print("Failures:", ", ".join(FAILURES))
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
