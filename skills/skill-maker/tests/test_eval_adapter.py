import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.eval_adapter import AdapterError, CommandAdapter, PROTOCOL
from scripts.eval_store import EvidenceStore


class TestCommandAdapter(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.output = self.tmp / "outputs"
        self.output.mkdir()
        self.request = {"protocol": PROTOCOL, "operation": "task", "output_dir": str(self.output)}

    def test_accepts_one_valid_response(self):
        code = "import json,sys; json.loads(sys.stdin.read()); print(json.dumps({'protocol':'skill-eval/v1','status':'ok','final':'ok','files':[]}))"
        result = CommandAdapter([sys.executable, "-c", code]).run(self.request)
        self.assertEqual(result.response["final"], "ok")

    def test_rejects_file_outside_output_directory(self):
        code = "import json; print(json.dumps({'protocol':'skill-eval/v1','status':'ok','files':['../escape']}))"
        with self.assertRaises(AdapterError):
            CommandAdapter([sys.executable, "-c", code]).run(self.request)

    def test_timeout_is_an_adapter_error(self):
        code = "import time; time.sleep(2)"
        with self.assertRaises(AdapterError):
            CommandAdapter([sys.executable, "-c", code], timeout_seconds=1).run(self.request)

    def test_nonzero_process_is_an_adapter_error(self):
        code = "import sys; sys.stderr.write('bad'); sys.exit(3)"
        with self.assertRaises(AdapterError):
            CommandAdapter([sys.executable, "-c", code]).run(self.request)


class TestEvidenceStore(unittest.TestCase):
    def test_audit_log_is_metadata_only_and_append_only(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        store = EvidenceStore(root, session_id="session")
        store.append_audit("task", "run", "adapter", True, "allow", "policy", "passed", [root / "runs" / "run"])
        store.append_audit("judge", "run", "adapter", False, "deny", "policy", "denied")
        lines = (root / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        payload = json.loads(lines[0])
        self.assertEqual(payload["session_id"], "session")
        self.assertNotIn("prompt", payload)
        self.assertNotIn("transcript", payload)
        self.assertNotIn("rubric", payload)


if __name__ == "__main__":
    unittest.main()
