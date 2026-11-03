# Evaluation protocol — Building 59 by-target transformation benchmark

Version 1.0 (2026-10-31). Applies to this repository (exported from `Building59-Benchmark-v2/`). Implemented by `evaluator/evaluate.py`
(grading) and `runners/build_prompt.py` (model input). The pass/fail rule is identical to the evaluator used for
all experiments reported so far (`eval_v3.1`), so earlier results stay comparable.
Paths under `src/` and `results/` refer to the research code, which is not part of this repository.

## 1. What a case is

A case asks: *given a sample of source data and a few rows of the target table, write a program that converts
any day of this source data into the target table.* The model gets no instructions in words.

```
<split>/TypeN/CaseNNN/
├── input/                      everything here is given to the model; nothing else is
│   ├── source_example/<file>.csv   source rows behind the 5 example target rows (example day)
│   ├── target_examples.csv         5 rows of the correct output for the example day
│   ├── task_input.json             target columns (name, type, unit), file names, row counts
│   └── selected_facts.txt          knowledge, only in the selected_facts condition
└── hidden/                     grader and researcher only; never shown to the model
    ├── source_test/<file>.csv      source data for the two test days (the program reads this at run time)
    ├── ground_truth.csv            correct output for the test days
    ├── reference_solution.py       the researcher's correct program
    ├── target_example_full.csv     all rows of the correct output for the example day
    └── task.json                   full task spec: generation rule, group lists, dates, needed facts
```

| File | Model sees it | Model's program reads it | Grader uses it |
|---|---|---|---|
| `input/*` | yes | no | no |
| `hidden/source_test/` | no | yes, at run time | yes (to run the program) |
| `hidden/ground_truth.csv` | no | no | yes |
| `hidden/reference_solution.py`, `task.json`, `target_example_full.csv` | no | no | no (provenance) |

`kg/full_knowledge_base.txt` (data dictionary + Brick model, 60,588 characters, identical for every case) is given
to the model only in the `full_kb` condition.

## 2. How the data is split

**Inside each case** (one source CSV, or 2–3 for Type3):

| Part | Days | Produces |
|---|---|---|
| Example split | 1 day | `source_example` → (correct program) → `target_examples` (5 of 48/24 rows shown) |
| Held-out split | 2 consecutive days | `source_test` → (correct program) → `ground_truth` |

- Only "clean" days are used: complete rows, no duplicate timestamps, no missing values in the columns used.
- The example day is at least 30 days away from the test days.
- The 5 shown rows are not the first 5: they are chosen so that every listed wrong approach for the case
  (wrong aggregation, unconverted unit, outer join, shuffled groups, …) gives a different value in at least one of
  them. With these 5 rows the correct transformation is identifiable.

**Across the benchmark:**

| Set | Cases | Rule |
|---|---|---|
| `dev/` | 293 (Type1 133, Type2 34, Type3 85, Type4 41) | used while building the prompt, grader and probe |
| `held_out/` | 308 (Type1 134, Type2 31, Type3 83, Type4 60) | generated after development, on (file, date) pairs that no dev case uses; Type4 Case042–060 are new aggregation combinations not in dev. Frozen (sha256) before any model was run on them. |

Generation is deterministic: fixed rules plus a fixed random seed (`src/s05_generate.py`, `s35`, `s39`).
`manifest.csv` maps each case to its original task id.

## 3. Model input

The prompt is built from `input/` (and `kg/`) only: `python runners/build_prompt.py <case> <condition>`.
It contains, in order: the source rows, the target schema (column, type, unit), the 5 target rows, the knowledge
block if any, and the output contract.

| Condition | Knowledge block |
|---|---|
| `none` | — |
| `full_kb` | `kg/full_knowledge_base.txt` |
| `selected_facts` | `input/selected_facts.txt`: every known fact about the columns this case uses (unit, class, floor, RTU, VAV, …), ≤ 4,000 characters. This is an **oracle upper bound** for retrieval, not a retriever's output. |

Never given to the model: the generation rule or any text description of the task, the column descriptions,
which rows were chosen, test-day data, ground truth, the reference program.

## 4. Model output and execution

The model returns `def transform(sources: dict) -> pandas.DataFrame` (pandas/numpy only), where `sources` maps each
source file name to a path. (A SQL variant exists: one DuckDB query; see `build_prompt.py --lang sql`.)

The program is run once on `hidden/source_test/` with a 120 s limit. In our experiments it ran in a bubblewrap
sandbox (no network, only copies of the test source files visible, no access to answers or keys).
`evaluate.py --program` runs it in a plain subprocess, which is **not** a security sandbox.

Run statuses: `ok`, `exception`, `timeout`, `no_output`, `unparseable`, `no_code`. Any status other than `ok` scores
0 on every metric below. Grader failures are never counted as model failures.

## 5. How the output is compared

Before comparing, both tables are canonicalised:

1. **Timestamps** are parsed and rewritten as `YYYY-MM-DD HH:MM:SS`; any parseable format is accepted for scoring.
2. **Row order is ignored**: both tables are sorted by timestamp, and rows are matched by timestamp.
3. **Column order is ignored for scoring**; columns are matched by exact name.
4. **Numbers**: a value is correct if `|pred − truth| ≤ 1e-6 + 1e-3 · |truth|` (relative tolerance 0.1 %).
5. **Missing values**: a missing predicted value is never correct. No ground-truth file contains missing values
   (checked: 0 of 601).

## 6. Metrics

| Metric | Definition | Notes |
|---|---|---|
| **Exact match** (= *pass*) | same column set, same timestamps (same row count, no duplicates), every value within tolerance | the number reported in all results so far |
| **Column accuracy** | share of target value columns whose every value is correct | in Type4 each column is one group (e.g. RTU01), so this is a per-group score |
| **Value accuracy** | correct cells ÷ (target cells + extra rows × value columns) | see score policy below |
| **Group accuracy** (Type4) | whether the program's room-to-group assignment equals Brick, read with a probe (fake data with marked rooms) | diagnostic, `src/s43_t4_membership_probe_v2.py`; not part of `evaluate.py` |
| Output contract | exact column order, `YYYY-MM-DD HH:MM:SS` strings, no duplicate timestamps or columns | reported separately; not part of exact match |
| Execution time | wall-clock seconds of the program on the test days | `evaluate.py --program` |
| Generation time | seconds from request to model answer | recorded by the runner (`eval.json` → `seconds`) |

**Score policy when shapes differ** (so a partial table can never score higher than it deserves):

| Situation | Exact match | Value accuracy |
|---|---|---|
| missing column | fail | its cells count as wrong |
| extra column | fail | not counted |
| missing row | fail | its cells count as wrong |
| extra row (timestamp not in truth) | fail | adds its cells to the denominator as wrong |
| duplicated timestamp | fail | that timestamp's cells count as wrong |
| program fails / no output | fail | 0 |

## 7. Checks run on this release (`src/s49_verify_v2_layout.py`, results in `results/s49_verify/`)

| Check | Result |
|---|---|
| Prompts rebuilt from `input/` equal the experiment code's prompts: 601 cases × 3 conditions × {Python, SQL} | 3,606 / 3,606 identical |
| Equal to the prompts actually sent in experiment Q1 (`prompt.md`) | 360 / 360 identical |
| `input/` holds only the allowed files; no test-day date, non-shown example row or task description inside | 601 / 601 clean |
| Reference programs run on the test days and graded by `evaluate.py` | 601 / 601 exact match, value accuracy 1.0, contract pass |
| 9 kinds of altered outputs per case (rows shuffled, columns reordered, one cell 1 % off, within tolerance, row dropped, row duplicated, extra column, missing column, other timestamp format), graded by `evaluate.py` and by `eval_v3.1` | 5,409 gradings: all as expected, 0 disagreements between the two evaluators |

## 8. Points to confirm

1. Tolerance: 0.1 % relative (+1e-6 absolute) — acceptable?
2. Should the output contract (column order, timestamp format) count toward pass? Currently reported separately.
3. Value accuracy penalises extra rows in the denominator — acceptable?
4. Group accuracy uses a probe; should it stay a diagnostic or become a headline metric?
