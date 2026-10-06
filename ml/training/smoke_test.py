import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ml.inference import predict, model_info, top_terms_by_class

print("MODEL INFO:", json.dumps(model_info(), indent=2))
print("\n--- sanity predictions ---")
samples = [
    "I absolutely love this product, it is amazing and works perfectly!",
    "This is the worst experience I have ever had. Terrible service.",
    "The package arrived on Tuesday. It contains three items.",
    "",
]
for s in samples:
    if not s.strip():
        continue
    r = predict(s)
    print(f"[{r['prediction']}] conf={r['confidence']:.3f} :: {s[:50]}")
    print("   why:", r["simple_explanation"][:160])
    print("   terms:", [t["term"] for t in r["technical_details"]["influential_terms"][:5]])

print("\n--- top terms ---")
tt = top_terms_by_class(top_k=8)
for k, v in tt.items():
    print(f"{k}: {v}")
