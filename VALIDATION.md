# Publication validation

Validated on Windows with Python 3.13.5, pandas 2.2.3 and NumPy 2.1.3 before the initial publication.
These checks use the bundled reference programs and local data; no model API calls are needed.

| Check | Result |
|---|---:|
| Manifest has unique cases and expected split/type counts | 601 / 601 |
| Data, knowledge, prompt builder and original evaluator match the prepared v2 export byte-for-byte | 5,853 files |
| Rebuilt prompts match the prepared v2 export (3 conditions × 2 languages) | 3,606 / 3,606 |
| Input file allowlist, five target examples, and no test-day dates or task instruction in input | 601 / 601 |
| Reference transforms run in-process and pass exact match, value accuracy and output contract | 601 / 601 |
| Nine grading perturbations per case produce the expected pass/fail | 5,409 / 5,409 |
| Public evaluator subprocess path, one reference program per task type | 4 / 4 |
| Batch evaluator tests: missing/invalid predictions, split/type selection, broken ground truth | 4 / 4 |

Run the batch evaluator tests from the repository root:

```sh
python -B -m unittest discover -s tests -v
```

Run a reference-program smoke check (for verification only; reference programs must not be supplied to a model):

```sh
python evaluator/evaluate.py --case dev/Type4/Case001 --program dev/Type4/Case001/hidden/reference_solution.py
```

The initial scientific checks against the research runner and historical model prompts are documented separately
in [evaluation_protocol.md](evaluation_protocol.md#7-checks-run-on-this-release-srcs49_verify_v2_layoutpy-results-in-resultss49_verify).
