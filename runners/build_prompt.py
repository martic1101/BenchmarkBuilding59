"""Build the model prompt for one case using ONLY the files in <case>/input/ and ../kg/.
This is the exact prompt used in the Building 59 experiments (prompt version v2_aligned).

Usage: python build_prompt.py <case_dir> <none|full_kb|selected_facts> [--lang python|sql]
Knowledge conditions:
  none            no knowledge block
  full_kb         kg/full_knowledge_base.txt (data dictionary + Brick model, same for every case)
  selected_facts  <case>/input/selected_facts.txt (all facts about the columns this case uses;
                  an oracle upper bound, not a retrieval result)
"""
import json, sys
from pathlib import Path

SYSTEM = ("You are a data engineer. You write correct, self-contained Python (pandas/numpy only) that transforms "
          "building time-series CSV files into a requested target table.")
CONTRACT = """Write a Python function:

    def transform(sources: dict) -> pandas.DataFrame

`sources` maps each source file name (e.g. "rtu_sa_t.csv") to a local file path. The files have the same format as the
samples above but contain more rows (whole days). Return a DataFrame with exactly the target columns, in order. The
`timestamp` column must be a string 'YYYY-MM-DD HH:MM:SS'. Use only pandas and numpy. Do not print anything.
Answer with one ```python code block."""
SYSTEM_SQL = ("You are a data engineer. You write correct, self-contained SQL (DuckDB dialect) that transforms "
              "building time-series data into a requested target table.")
CONTRACT_SQL = """Write one DuckDB SQL query (a SELECT; WITH clauses are allowed).

Each source file is loaded as a table named after the file without ".csv" (e.g. "rtu_sa_t.csv" -> table rtu_sa_t). The
tables have the same columns as the samples above but contain more rows (whole days). The first column holds the
timestamp text exactly as it appears in the file (VARCHAR); every other column is DOUBLE, with missing values as NULL.
The query must return exactly the target columns, in order. The `timestamp` column must be a string
'YYYY-MM-DD HH:MM:SS'. The query cannot read files or create anything outside this database.
Answer with one ```sql code block."""
CONDITIONS = ("none", "full_kb", "selected_facts")


def build_prompt(case_dir, cond="none", lang="python", kg_dir=None):
    case_dir = Path(case_dir); inp = case_dir / "input"
    if cond not in CONDITIONS: raise ValueError(f"cond must be one of {CONDITIONS}")
    kg_dir = Path(kg_dir) if kg_dir else case_dir.parents[2] / "kg"
    meta = json.loads((inp / "task_input.json").read_text(encoding="utf-8"))
    parts = ["## Source files"]
    for f in meta["source_files"]:
        lines = (inp / "source_example" / f).read_text(encoding="utf-8").splitlines()
        header, data, out, i = lines[0], lines[1:], [lines[0]], 0
        for b, size in enumerate(meta["source_blocks"][f]):
            if b: out.append("...")
            out += data[i:i + size]; i += size
        assert i == len(data), f"{f}: block sizes do not match the file"
        txt = "\n".join(out) + "\n"
        parts.append(f"### {f} — the {len(data)} source rows (of {meta['n_example_day_source_rows'][f]} for the example day) "
                     f"that fall in the intervals of the example target rows below\n```\n{txt}```")
    parts.append("## Target table schema")
    rows = ["| column | type | unit |", "|---|---|---|"]
    rows += [f"| {c['name']} | {c['dtype']} | {c.get('unit', '')} |" for c in meta["target_schema"]]
    parts.append("\n".join(rows))
    tgt = (inp / "target_examples.csv").read_text(encoding="utf-8")
    n_shown = len(tgt.splitlines()) - 1
    parts.append(f"## Example target rows ({n_shown} of the {meta['n_example_day_target_rows']} rows the target table has "
                 f"for the example day {meta['example_day']})\n```\n{tgt}```")
    kb = ""
    if cond == "full_kb": kb = (kg_dir / "full_knowledge_base.txt").read_text(encoding="utf-8")
    if cond == "selected_facts": kb = (inp / "selected_facts.txt").read_text(encoding="utf-8")
    if kb:
        parts.append("## Background knowledge (may be incomplete or contain errors)\n" + kb)
    parts.append("## What to write\n" + (CONTRACT if lang == "python" else CONTRACT_SQL))
    return (SYSTEM if lang == "python" else SYSTEM_SQL), "\n\n".join(parts)


if __name__ == "__main__":
    a = sys.argv[1:]
    lang = a[a.index("--lang") + 1] if "--lang" in a else "python"
    system, user = build_prompt(a[0], a[1] if len(a) > 1 and not a[1].startswith("--") else "none", lang)
    print("# SYSTEM\n" + system + "\n\n# USER\n" + user)
