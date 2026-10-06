"""Generate a human-readable model evaluation report from saved metrics.

Run:
    python -m ml.evaluation.report
Writes reports/model_report.md and prints a comparison table.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.config import METRICS_FILE, REPORTS_DIR  # noqa: E402


def main() -> int:
    if not METRICS_FILE.exists():
        print("No metrics found. Run: python -m ml.training.train")
        return 1
    m = json.loads(METRICS_FILE.read_text(encoding="utf-8"))
    dataset = m.get("dataset", {})
    models = m.get("models", {})

    lines: list[str] = []
    lines.append("# Model Evaluation Report\n")
    lines.append(f"- Dataset size: **{dataset.get('n_total', 0):,}** samples")
    lines.append(f"- Train / Test: **{dataset.get('n_train', 0):,}** / **{dataset.get('n_test', 0):,}**")
    lines.append(f"- Classes: {', '.join(dataset.get('classes', []))}")
    lines.append(f"- Chosen configuration: `{m.get('chosen_config')}`\n")

    lines.append("## Model comparison\n")
    lines.append("| Model | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) | F1 (weighted) | ROC-AUC |")
    lines.append("|---|---|---|---|---|---|---|")
    for name, met in models.items():
        auc = met.get("roc_auc_ovr_macro")
        auc_str = f"{auc*100:.2f}%" if auc is not None else "—"
        lines.append(
            f"| {name} | {met['accuracy']*100:.2f}% | {met['precision_macro']*100:.2f}% | "
            f"{met['recall_macro']*100:.2f}% | {met['f1_macro']*100:.2f}% | "
            f"{met['f1_weighted']*100:.2f}% | {auc_str} |"
        )

    lines.append("\n## Cross-validation (f1_macro, 3-fold)\n")
    lines.append("| Configuration | Mean F1 | Std |")
    lines.append("|---|---|---|")
    for cfg, res in m.get("configs_cv", {}).items():
        lines.append(f"| {cfg} | {res['mean_f1_macro']:.4f} | {res['std']:.4f} |")

    for name, met in models.items():
        cm = met.get("confusion_matrix")
        classes = met.get("classes", [])
        if not cm:
            continue
        lines.append(f"\n## {name} — confusion matrix\n")
        lines.append("| actual \\ predicted | " + " | ".join(classes) + " |")
        lines.append("|" + "---|" * (len(classes) + 1))
        for i, row in enumerate(cm):
            lines.append(f"| **{classes[i]}** | " + " | ".join(str(v) for v in row) + " |")

    report = "\n".join(lines) + "\n"
    out = REPORTS_DIR / "model_report.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
