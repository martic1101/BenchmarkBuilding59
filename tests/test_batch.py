"""Batch scoring keeps missing/invalid submissions in the selected case denominator."""
import csv
from pathlib import Path
import tempfile
import unittest

from evaluator.evaluate_batch import evaluate_batch


class BatchEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.predictions = self.root / "predictions"
        self.table = "timestamp,value\n2020-01-01 00:00:00,10.0\n"
        self.paths = ["held_out/Type1/Case001", "held_out/Type1/Case002", "dev/Type2/Case001"]
        with (self.root / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["split", "type", "path"])
            writer.writeheader()
            for path in self.paths:
                split, kind, _ = path.split("/")
                writer.writerow(dict(split=split, type=kind, path=path))
                truth = self.root / path / "hidden" / "ground_truth.csv"
                truth.parent.mkdir(parents=True)
                truth.write_text(self.table, encoding="utf-8")

    def predict(self, case, raw):
        path = self.predictions / Path(case).with_suffix(".csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw, encoding="utf-8")

    def test_missing_submission_is_zero_and_stays_in_denominator(self):
        self.predict(self.paths[0], self.table)
        result = evaluate_batch(self.root, self.predictions)
        self.assertEqual(result["n_cases"], 2)
        self.assertEqual(result["n_provided"], 1)
        self.assertEqual(result["n_passed"], 1)
        self.assertEqual(result["exact_match_rate"], 0.5)
        self.assertEqual(result["mean_value_accuracy"], 0.5)

    def test_malformed_and_non_utf8_submissions_score_zero(self):
        self.predict(self.paths[0], "not,a,predicted,table\n")
        self.predict(self.paths[1], self.table)
        (self.predictions / Path(self.paths[1]).with_suffix(".csv")).write_bytes(b"\xff\xfe\x00")
        result = evaluate_batch(self.root, self.predictions)
        self.assertEqual(result["n_cases"], 2)
        self.assertEqual(result["n_passed"], 0)
        self.assertEqual(result["mean_value_accuracy"], 0)
        self.assertEqual(result["cases"][1]["prediction_status"], "unreadable")

    def test_type_and_split_filter(self):
        self.predict(self.paths[2], self.table)
        result = evaluate_batch(self.root, self.predictions, "dev", "Type2")
        self.assertEqual(result["n_cases"], 1)
        self.assertEqual(result["exact_match_rate"], 1)

    def test_empty_selection_and_broken_ground_truth_raise(self):
        with self.assertRaises(ValueError):
            evaluate_batch(self.root, self.predictions, "dev", "Type4")
        (self.root / self.paths[0] / "hidden" / "ground_truth.csv").unlink()
        with self.assertRaises(FileNotFoundError):
            evaluate_batch(self.root, self.predictions)


if __name__ == "__main__":
    unittest.main()
