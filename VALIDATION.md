# Publication validation

Validated on Windows with Python 3.13.5, pandas 2.2.3 and NumPy 2.1.3 before the initial publication.
These checks use the bundled reference programs and local data; no model API calls are needed.

| Check | Result |
|---|---:|
| Manifest has unique cases and expected split/type counts | 601 / 601 |
| Initial working-tree copies matched the prepared v2 export byte-for-byte (not a Git-blob check; see correction below) | 5,853 files |
| Rebuilt prompts match the prepared v2 export (3 conditions × 2 languages) | 3,606 / 3,606 |
| Input file allowlist, five target examples, and no test-day dates or task instruction in input | 601 / 601 |
| Reference transforms run in-process and pass exact match, value accuracy and output contract | 601 / 601 |
| Nine grading perturbations per case produce the expected pass/fail | 5,409 / 5,409 |
| Public evaluator subprocess path, one reference program per task type | 4 / 4 |
| Batch evaluator tests: missing/invalid predictions, split/type selection, broken ground truth | 4 / 4 |

## Correction: validate stored Git bytes

The initial publication (`2b8cdab`) checked working-tree copies only. Its attributes normalized line endings
when staging files, so 819 `hidden/source_test/*.csv` Git blobs differed from the original export, solely by
CRLF-to-LF conversion. The other 5,034 compared files were identical. The original byte-identity statement
did not establish that the committed data matched; the table above now states that limitation explicitly.

The correction changes `.gitattributes` to `* -text` and restages the original, unmodified export bytes.
Raw Git blobs in the corrected commit were compared directly with the prepared export using `git cat-file
--batch`, without checkout or text-conversion filters: **5,853 / 5,853 files match byte-for-byte**, including
**819 / 819 test-source CSVs**. The excluded export files are its root `README.md` (edited for publication)
and `.export_complete` (not published). The original evaluator, prompt builder and numerical data are unchanged.

To reproduce the comparison when the original prepared v2 export is available:

```sh
python -B tests/verify_export_bytes.py --source /path/to/Building59-Benchmark-v2 --ref HEAD
```

Use `--index` instead of `--ref HEAD` to check staged blobs before committing. The tool exits nonzero if
any expected file is missing or differs, and reports newline-only differences separately. The initial
scientific checks above are historical results; this correction separately rechecks stored bytes, the batch
tests, and the evaluator subprocess path on one reference program per type.

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
