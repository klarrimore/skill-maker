"""Provider-neutral JSONL command adapter for skill evaluation."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


PROTOCOL = "skill-eval/v1"
MAX_STDOUT_BYTES = 2 * 1024 * 1024
MAX_STDERR_BYTES = 16 * 1024


class AdapterError(RuntimeError):
    """Raised when an adapter cannot produce a valid protocol response."""


@dataclass
class AdapterResult:
    response: Dict[str, Any]
    stderr: str = ""


class CommandAdapter:
    """Run an explicitly configured executable using one JSON request/response."""

    def __init__(self, argv: List[str], timeout_seconds: int = 300):
        if not argv or not all(isinstance(arg, str) and arg for arg in argv):
            raise ValueError("adapter argv must be a non-empty string array")
        if not isinstance(timeout_seconds, int) or timeout_seconds < 1 or timeout_seconds > 3600:
            raise ValueError("adapter timeout must be between 1 and 3600 seconds")
        self.argv = list(argv)
        self.timeout_seconds = timeout_seconds

    @property
    def executable(self) -> str:
        return self.argv[0]

    def run(self, request: Dict[str, Any]) -> AdapterResult:
        if not isinstance(request, dict) or request.get("protocol") != PROTOCOL:
            raise AdapterError("adapter request must use protocol {}".format(PROTOCOL))
        request_json = json.dumps(request, sort_keys=True) + "\n"
        env = {}
        if "PATH" in os.environ:
            env["PATH"] = os.environ["PATH"]
        if "PYTHONPATH" in os.environ:
            env["PYTHONPATH"] = os.environ["PYTHONPATH"]
        try:
            completed = subprocess.run(
                self.argv,
                input=request_json,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                timeout=self.timeout_seconds,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdapterError("adapter timed out after {} seconds".format(self.timeout_seconds)) from exc
        except OSError as exc:
            raise AdapterError("could not start adapter: {}".format(exc)) from exc

        stderr = (completed.stderr or "")[:MAX_STDERR_BYTES]
        stdout = completed.stdout or ""
        if len(stdout.encode("utf-8", errors="replace")) > MAX_STDOUT_BYTES:
            raise AdapterError("adapter stdout exceeds the {} byte limit".format(MAX_STDOUT_BYTES))
        if completed.returncode != 0:
            detail = stderr.strip() or "no stderr"
            raise AdapterError("adapter exited with {}: {}".format(completed.returncode, detail))
        try:
            response = json.loads(stdout)
        except ValueError as exc:
            raise AdapterError("adapter stdout is not exactly one JSON object") from exc
        if not isinstance(response, dict):
            raise AdapterError("adapter response must be a JSON object")
        self._validate_response(response, request)
        return AdapterResult(response=response, stderr=stderr)

    @staticmethod
    def _validate_response(response: Dict[str, Any], request: Dict[str, Any]) -> None:
        if response.get("protocol") != PROTOCOL:
            raise AdapterError("adapter response has the wrong protocol")
        status = response.get("status")
        if status not in {"ok", "error"}:
            raise AdapterError("adapter response status must be ok or error")
        if status == "error":
            if not isinstance(response.get("error"), str) or not response["error"].strip():
                raise AdapterError("error responses must include a non-empty error")
            return
        if "error" in response and response["error"] is not None:
            raise AdapterError("successful adapter responses cannot include an error")
        if "final" in response and not isinstance(response["final"], str):
            raise AdapterError("adapter final must be a string when present")
        if "transcript" in response and not isinstance(response["transcript"], (str, list)):
            raise AdapterError("adapter transcript must be a string or array")
        files = response.get("files", [])
        if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
            raise AdapterError("adapter files must be a string array")
        output_dir = request.get("output_dir")
        if not isinstance(output_dir, str) or not output_dir:
            raise AdapterError("adapter request must include output_dir")
        root = Path(output_dir).resolve()
        for item in files:
            path = Path(item)
            candidate = path if path.is_absolute() else root / path
            candidate = candidate.resolve()
            try:
                candidate.relative_to(root)
            except ValueError as exc:
                raise AdapterError("adapter file escapes output_dir: {}".format(item)) from exc
        metrics = response.get("metrics", {})
        if metrics is not None and not isinstance(metrics, dict):
            raise AdapterError("adapter metrics must be an object")


def error_response(message: str) -> Dict[str, Any]:
    """Create an explicit failed response for a process/protocol failure."""
    return {"protocol": PROTOCOL, "status": "error", "error": message}
