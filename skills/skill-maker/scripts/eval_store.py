"""Workspace-owned evidence and metadata-only audit logging."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


AUDIT_FIELDS = {
    "timestamp",
    "session_id",
    "run_id",
    "operation",
    "adapter",
    "allow",
    "decision",
    "policy",
    "status",
    "artifacts",
}


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError("not JSON serializable: {}".format(type(value).__name__))


def atomic_write_json(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".{}.".format(path.name), dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, default=_json_default)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class EvidenceStore:
    """Persist run artifacts below one resolved workspace and append safe metadata."""

    def __init__(self, workspace: Path, session_id: Optional[str] = None):
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.session_id = session_id or self.workspace.name
        self.audit_path = self.workspace / "audit.jsonl"

    def contained(self, path: Path) -> Path:
        resolved = Path(path).resolve()
        try:
            resolved.relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError("workspace path escapes workspace: {}".format(path)) from exc
        return resolved

    def run_dir(self, run_id: str) -> Path:
        if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
            raise ValueError("run_id must be a single safe path component")
        path = self.contained(self.workspace / "runs" / run_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_run(self, run_id: str, request: Dict[str, Any], response: Dict[str, Any], result: Dict[str, Any]) -> Path:
        directory = self.run_dir(run_id)
        atomic_write_json(directory / "request.json", request)
        atomic_write_json(directory / "response.json", response)
        atomic_write_json(directory / "grading.json", result)
        return directory

    def write_json(self, relative_name: str, value: Any) -> Path:
        path = self.contained(self.workspace / relative_name)
        atomic_write_json(path, value)
        return path

    def append_audit(
        self,
        operation: str,
        run_id: str,
        adapter: str,
        allow: bool,
        decision: str,
        policy: str,
        status: str,
        artifacts: Optional[list] = None,
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "run_id": run_id,
            "operation": operation,
            "adapter": adapter,
            "allow": bool(allow),
            "decision": decision,
            "policy": policy,
            "status": status,
            "artifacts": [str(item) for item in (artifacts or [])],
        }
        # Construct the record from a fixed allowlist. Prompts, transcripts,
        # rubrics, credentials, and environment variables cannot enter this file.
        entry = {key: entry[key] for key in AUDIT_FIELDS}
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
