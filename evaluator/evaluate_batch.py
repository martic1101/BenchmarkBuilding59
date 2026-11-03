"""Grade a directory of predicted CSVs; no model calls or program execution.

Prediction paths mirror the benchmark: predictions/held_out/Type4/Case001.csv.
Missing and malformed predictions remain in the denominator and score zero.
"""
import argparse
import csv
import json
from pathlib import Path

import pandas as pd

try:
    from .evaluate import grade
except ImportError:
    from evaluate import grade

ROOT = Path(__file__).resolve().parents[1]


def evaluate_batch(root, predictions, split="held_out", task_type=None):
    root, predictions = Path(root), Path(predictions)
    with (root / "manifest.csv").open(encoding="utf-8", newline="") as f:
        cases = [r for r in csv.DictReader(f)
                 if r["split"] == split and (task_type is None or r["type"] == task_type)]
    if not cases:
        raise ValueError("No cases matched the requested split/type")
    results = []
    for case in cases:
        case_path = Path(case["path"])
        pred = predictions / case_path.with_suffix(".csv")
        # Broken ground truth raises an error instead of counting as a model failure.
        target = pd.read_csv(root / case_path / "hidden" / "ground_truth.csv")
        raw, status = None, "missing"
        if pred.exists():
            try:
                raw = pred.read_text(encoding="utf-8-sig")
                status = "provided"
            except (OSError, UnicodeError) as exc:
                status = "unreadable"
                read_error = str(exc)
        result = grade(raw, target)
        if status == "unreadable":
            result["reason"] = read_error
        result.update(case=case["path"], type=case["type"], prediction_status=status)
        results.append(result)
    by_type = {t: _summary([r for r in results if r["type"] == t])
               for t in sorted({r["type"] for r in results})}
    return {"split": split, "type": task_type or "all", **_summary(results), "by_type": by_type, "cases": results}


def _summary(results):
    n = len(results)
    return {
        "n_cases": n,
        "n_provided": sum(r["prediction_status"] == "provided" for r in results),
        "n_passed": sum(r["exact_match"] for r in results),
        "exact_match_rate": sum(r["exact_match"] for r in results) / n,
        "mean_column_accuracy": sum(r["column_accuracy"] for r in results) / n,
        "mean_value_accuracy": sum(r["value_accuracy"] for r in results) / n,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--predictions", type=Path, required=True)
    ap.add_argument("--split", choices=("dev", "held_out"), default="held_out")
    ap.add_argument("--type", choices=("Type1", "Type2", "Type3", "Type4"))
    ap.add_argument("--out", type=Path, help="Optional full JSON report path")
    args = ap.parse_args()
    report = evaluate_batch(args.root, args.predictions, args.split, args.type)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
