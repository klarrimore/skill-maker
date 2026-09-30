import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.eval_models import EvalSchemaError, load_eval_suite, load_trigger_queries

ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT / "evals" / "files" / "eval-suite-valid"


class TestEvalModels(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_valid_suite_has_typed_expectations(self):
        suite = load_eval_suite(VALID)
        self.assertEqual({case.split for case in suite.evals}, {"train", "held_out"})
        self.assertEqual([item.kind for item in suite.evals[0].expectations], ["text_contains", "file_exists", "json_value"])

    def test_path_escape_is_rejected_before_execution(self):
        data = json.loads((VALID / "evals" / "evals.json").read_text(encoding="utf-8"))
        data["evals"][0]["files"] = ["../../outside.txt"]
        fixture = self.tmp / "skill"
        shutil.copytree(str(VALID), str(fixture))
        (fixture / "evals" / "evals.json").write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(EvalSchemaError):
            load_eval_suite(fixture)

    def test_unknown_field_is_rejected(self):
        data = json.loads((VALID / "evals" / "evals.json").read_text(encoding="utf-8"))
        data["evals"][0]["expectations"][0]["unexpected"] = True
        fixture = self.tmp / "skill"
        shutil.copytree(str(VALID), str(fixture))
        (fixture / "evals" / "evals.json").write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(EvalSchemaError):
            load_eval_suite(fixture)

    def test_trigger_contract_requires_versioned_object(self):
        fixture = self.tmp / "skill"
        shutil.copytree(str(VALID), str(fixture))
        (fixture / "evals" / "trigger_queries.json").write_text("[]", encoding="utf-8")
        with self.assertRaises(EvalSchemaError):
            load_trigger_queries(fixture)


if __name__ == "__main__":
    unittest.main()
