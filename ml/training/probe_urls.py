import requests, time, uuid
BASE = "http://127.0.0.1:8000/api"
email = f"probe_{uuid.uuid4().hex[:10]}@example.com"
r = requests.post(f"{BASE}/auth/register", json={"full_name":"Probe User","email":email,"password":"DemoPass123","confirm_password":"DemoPass123"})
tok = r.json()["access_token"]; h = {"Authorization": f"Bearer {tok}"}
for u in [
    "https://www.apnews.com",
    "https://textfiles.com/100/",
    "https://www.reuters.com",
    "https://arstechnica.com",
    "https://www.npr.org",
    "https://edition.cnn.com",
    "https://www.bbc.com/news/science_and_environment",
]:
    try:
        r = requests.post(f"{BASE}/analyze-url", json={"url": u}, headers=h, timeout=60)
        if r.status_code == 200:
            b = r.json()
            print(f"OK  {u} -> {b['overall_sentiment']} conf={b['confidence']:.2f} words={b['word_count']} title={b['title'][:45]!r}")
        else:
            print(f"ERR {u} -> {r.status_code} {r.text[:90]}")
    except Exception as e:
        print(f"EXC {u} -> {e}")
