"""Grade one predicted output table against a case's ground truth (Building 59 benchmark).
Implements evaluation_protocol.md. Same pass/fail rule as the experiments' evaluator (eval_v3.1), plus
value-level accuracy and column accuracy.

  python evaluate.py --case <case_dir> --pred predicted.csv            grade a CSV you already have
  python evaluate.py --case <case_dir> --program solution.py           run transform(sources) on hidden/source_test, then grade

--program runs the code in a plain subprocess with a time limit. It is NOT a security sandbox: run untrusted,
model-written code only inside an isolated environment (the experiments used bubblewrap, no network).
"""
import argparse, io, json, re, subprocess, sys, tempfile, time
from pathlib import Path
import numpy as np
import pandas as pd

RTOL, ATOL = 1e-3, 1e-6            # a value is correct if |pred - truth| <= ATOL + RTOL * |truth|
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
VERSION = "b59_eval_1.0 (pass rule identical to eval_v3.1)"


def _norm_ts(s):
    return pd.to_datetime(s.astype(str), errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")


def contract(raw_csv, target_cols):
    """Output contract stated in the prompt (reported separately; not part of exact_match)."""
    import csv
    rows = list(csv.reader(io.StringIO(raw_csv)))
    header = rows[0] if rows else []
    c = dict(columns_in_order=header == target_cols, duplicate_columns=len(set(header)) != len(header))
    if "timestamp" in header:
        i = header.index("timestamp"); ts = [r[i] if i < len(r) else "" for r in rows[1:]]
        parsed = pd.to_datetime(pd.Series(ts, dtype=object), format="%Y-%m-%d %H:%M:%S", errors="coerce")
        c.update(ts_format_ok=all(TS_RE.match(x) for x in ts), ts_valid=bool(parsed.notna().all()),
                 duplicate_timestamps=int(parsed.duplicated().sum()), sorted=bool(parsed.is_monotonic_increasing))
    else:
        c.update(ts_format_ok=False, ts_valid=False, duplicate_timestamps=0, sorted=False)
    c["contract_pass"] = bool(c["columns_in_order"] and not c["duplicate_columns"] and c["ts_format_ok"]
                              and c["ts_valid"] and c["duplicate_timestamps"] == 0)
    return c


def grade(raw_csv, target):
    """raw_csv: the predicted table as CSV text (or None if the program produced nothing). target: ground-truth DataFrame."""
    tcols = [c for c in target.columns if c != "timestamp"]
    n_target_cells = len(target) * len(tcols)
    r = dict(eval_version=VERSION, executed=raw_csv is not None, exact_match=False, schema_ok=False, rows_ok=False,
             ts_ok=False, col_correct={c: False for c in tcols}, column_accuracy=0.0, value_accuracy=0.0,
             n_target_rows=len(target), n_pred_rows=0, n_missing_rows=len(target), n_extra_rows=0,
             n_target_cells=n_target_cells, n_correct_cells=0, reason="")
    if raw_csv is None:
        r["reason"] = "no output"; return r
    try:
        out = pd.read_csv(io.StringIO(raw_csv))
    except Exception as e:
        r["reason"] = f"unparseable output: {e!r}"[:200]; return r
    r["contract"] = contract(raw_csv, list(target.columns))
    r["n_pred_rows"] = len(out)
    if "timestamp" not in out.columns:
        r["reason"] = "missing timestamp column"; return r
    missing = [c for c in tcols if c not in out.columns]
    extra = [c for c in out.columns if c not in target.columns]
    r["schema_ok"] = not missing and not extra
    o, t = out.copy(), target.copy()
    o["timestamp"] = _norm_ts(o["timestamp"]); t["timestamp"] = _norm_ts(t["timestamp"])
    o = o.sort_values("timestamp", kind="stable").reset_index(drop=True)      # row order never matters
    t = t.sort_values("timestamp", kind="stable").reset_index(drop=True)
    r["rows_ok"] = len(o) == len(t)
    r["ts_ok"] = r["rows_ok"] and bool((o["timestamp"].values == t["timestamp"].values).all())
    # --- exact match: same rule as eval_v3.1 (column-wise, rows aligned by timestamp)
    if r["schema_ok"]:
        m = t.merge(o, on="timestamp", how="left", suffixes=("", "__out"))
        for c in tcols:
            a = pd.to_numeric(m[c + "__out"], errors="coerce").to_numpy(dtype=float)
            b = m[c].to_numpy(dtype=float)
            r["col_correct"][c] = bool(len(a) == len(b) and np.isclose(a, b, rtol=RTOL, atol=ATOL).all())
    else:
        for c in tcols:
            if c in o.columns:
                m = t[["timestamp", c]].merge(o[["timestamp", c]], on="timestamp", how="left", suffixes=("", "__out"))
                a = pd.to_numeric(m[c + "__out"], errors="coerce").to_numpy(dtype=float)
                r["col_correct"][c] = bool(len(m) == len(t) and np.isclose(a, m[c].to_numpy(dtype=float), rtol=RTOL, atol=ATOL).all())
    r["exact_match"] = bool(r["schema_ok"] and r["ts_ok"] and all(r["col_correct"].values()))
    r["column_accuracy"] = round(sum(r["col_correct"].values()) / len(tcols), 6) if tcols else 0.0
    # --- value accuracy: cell by cell; a target row counts only if the prediction has that timestamp exactly once
    counts = o["timestamp"].value_counts()
    uniq = o[o["timestamp"].map(counts) == 1].set_index("timestamp")
    tt = t.set_index("timestamp")
    present = tt.index.isin(uniq.index)
    r["n_missing_rows"] = int((~tt.index.isin(o["timestamp"])).sum())
    r["n_duplicate_timestamp_rows"] = int((o["timestamp"].map(counts) > 1).sum())
    r["n_extra_rows"] = int((~o["timestamp"].isin(tt.index)).sum())
    correct = 0
    for c in tcols:
        if c not in uniq.columns: continue
        a = pd.to_numeric(uniq.loc[tt.index[present], c], errors="coerce").to_numpy(dtype=float)
        b = tt.loc[present, c].to_numpy(dtype=float)
        correct += int(np.isclose(a, b, rtol=RTOL, atol=ATOL).sum())
    denom = n_target_cells + r["n_extra_rows"] * len(tcols)     # extra rows are penalised, never ignored
    r["n_correct_cells"] = correct
    r["value_accuracy"] = round(correct / denom, 6) if denom else 0.0
    if not r["exact_match"]:
        r["reason"] = "; ".join(x for x in [
            f"missing cols {missing}" if missing else "", f"extra cols {extra}" if extra else "",
            "" if r["rows_ok"] else f"rows {len(o)} vs {len(t)}", "" if r["ts_ok"] else "timestamps differ",
            f"wrong values in {[c for c, v in r['col_correct'].items() if not v]}" if not all(r["col_correct"].values()) else ""] if x)
    return r


HARNESS = r"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("solution", sys.argv[1]); mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
out = mod.transform(json.loads(sys.argv[2]))
out.to_csv(sys.argv[3], index=False)
"""


def run_program(program, case_dir, timeout=120):
    case_dir = Path(case_dir)
    task = json.loads((case_dir / "input" / "task_input.json").read_text(encoding="utf-8"))
    sources = {f: str((case_dir / "hidden" / "source_test" / f).resolve()) for f in task["source_files"]}
    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "harness.py"; h.write_text(HARNESS); out = Path(td) / "out.csv"
        t0 = time.time()
        try:
            p = subprocess.run([sys.executable, "-B", str(h), str(Path(program).resolve()), json.dumps(sources), str(out)],
                               capture_output=True, text=True, timeout=timeout, cwd=td)
            status = "ok" if p.returncode == 0 and out.exists() else "exception"; err = p.stderr[-800:]
        except subprocess.TimeoutExpired:
            status, err = "timeout", ""
        secs = round(time.time() - t0, 3)
        raw = out.read_text(encoding="utf-8") if status == "ok" else None
    return raw, dict(status=status, execution_seconds=secs, stderr=err)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--case", required=True)
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--pred"); g.add_argument("--program")
    ap.add_argument("--timeout", type=float, default=120); a = ap.parse_args()
    target = pd.read_csv(Path(a.case) / "hidden" / "ground_truth.csv")
    if a.pred:
        r = grade(Path(a.pred).read_text(encoding="utf-8"), target)
    else:
        raw, ex = run_program(a.program, a.case, a.timeout); r = grade(raw, target); r.update(ex)
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
