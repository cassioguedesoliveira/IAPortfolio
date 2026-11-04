import json
import tempfile
import unittest
from pathlib import Path

from evalkit.cli import main as cli_main
from evalkit.compare import compare_runs
from evalkit.dataset import Case, load_dataset
from evalkit.judge import make_judge_metric
from evalkit.metrics import contains, exact_match, json_fields, regex_match, token_f1
from evalkit.runner import run_eval


class MetricTests(unittest.TestCase):
    def test_exact_match_ignores_case_and_punctuation(self):
        self.assertEqual(exact_match("Paris!", "paris", {}), 1.0)
        self.assertEqual(exact_match("Lyon", "Paris", {}), 0.0)

    def test_contains(self):
        self.assertEqual(contains("It is Paris, of course.", "paris", {}), 1.0)

    def test_token_f1_partial_credit(self):
        score = token_f1("the cat sat", "the cat sat down", {})
        self.assertAlmostEqual(score, 2 * 1.0 * 0.75 / 1.75)

    def test_regex(self):
        self.assertEqual(regex_match("I can't do that", r"(can't|cannot)", {}), 1.0)

    def test_json_fields_with_fences_and_partial(self):
        out = '```json\n{"name": "Ana", "city": "Rio"}\n```'
        self.assertEqual(json_fields(out, '{"name": "Ana", "city": "Recife"}', {}), 0.5)
        self.assertEqual(json_fields("not json", '{"a": 1}', {}), 0.0)


class JudgeTests(unittest.TestCase):
    def test_score_normalisation_and_failure_modes(self):
        metric = make_judge_metric(lambda p: 'Sure: {"score": 5, "reason": "ok"}')
        self.assertEqual(metric("a", "a", {}), 1.0)
        self.assertEqual(make_judge_metric(lambda p: '{"score": 1}')("a", "b", {}), 0.0)
        self.assertEqual(make_judge_metric(lambda p: "no json here")("a", "b", {}), 0.0)
        self.assertEqual(make_judge_metric(lambda p: '{"score": "high"}')("a", "b", {}), 0.0)


class RunnerTests(unittest.TestCase):
    def test_crashing_model_is_recorded_not_raised(self):
        def flaky(prompt):
            raise TimeoutError("upstream timeout")

        result = run_eval("flaky", flaky, [Case("a", "q", "x", tags=("t",))])
        self.assertEqual(result.mean_score, 0.0)
        self.assertEqual(result.error_rate, 1.0)
        self.assertIn("TimeoutError", result.cases[0].error)

    def test_tag_aggregation(self):
        cases = [Case("1", "q1", "a", tags=("x",)), Case("2", "q2", "b", tags=("x", "y"))]
        result = run_eval("m", lambda q: "a" if q == "q1" else "wrong", cases)
        self.assertEqual(result.by_tag(), {"x": 0.5, "y": 0.0})


class DatasetTests(unittest.TestCase):
    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "d.jsonl"
            line = json.dumps({"id": "1", "input": "q", "expected": "a"})
            p.write_text(f"{line}\n{line}\n")
            with self.assertRaises(ValueError):
                load_dataset(p)


class RegressionTests(unittest.TestCase):
    def test_cli_detects_regression(self):
        with tempfile.TemporaryDirectory() as d:
            good, bad = str(Path(d) / "good.json"), str(Path(d) / "bad.json")
            self.assertEqual(cli_main(["run", "--dataset", "datasets/qa.jsonl", "--model",
                                       "examples.models:good_model", "--out", good]), 0)
            self.assertEqual(cli_main(["run", "--dataset", "datasets/qa.jsonl", "--model",
                                       "examples.models:worse_model", "--out", bad]), 0)
            self.assertEqual(cli_main(["compare", "--baseline", good, "--new", good]), 0)
            self.assertEqual(cli_main(["compare", "--baseline", good, "--new", bad]), 1)

    def test_compare_lists_regressed_cases(self):
        base = {"mean_score": 1.0, "by_tag": {"m": 1.0}, "cases": [{"id": "a", "score": 1.0}]}
        new = {"mean_score": 0.5, "by_tag": {"m": 0.5}, "cases": [{"id": "a", "score": 0.0}]}
        cmp = compare_runs(base, new, max_drop=0.02)
        self.assertFalse(cmp.passed)
        self.assertEqual(cmp.regressed_cases, ["a"])


if __name__ == "__main__":
    unittest.main()
