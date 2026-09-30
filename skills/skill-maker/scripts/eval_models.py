"""Versioned, strict models for skill evaluation data.

The evaluator deliberately validates all paths before an adapter is started.  This
keeps malformed evaluation data from becoming an execution-policy problem.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


EVAL_SCHEMA_VERSION = 1
TRIGGER_SCHEMA_VERSION = 1
EXPECTATION_KINDS = {
    "file_exists",
    "text_contains",
    "text_excludes",
    "regex",
    "json_value",
    "validator",
    "command",
    "judge",
}
SPLITS = {"train", "held_out"}


class EvalSchemaError(ValueError):
    """Raised when an evaluation contract is malformed or unsafe."""


def _require_mapping(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise EvalSchemaError("{} must be an object".format(label))
    return value


def _require_string(value: Any, label: str, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise EvalSchemaError("{} must be a non-empty string".format(label))
    return value


def _require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise EvalSchemaError("{} must be a boolean".format(label))
    return value


def _require_list(value: Any, label: str) -> List[Any]:
    if not isinstance(value, list):
        raise EvalSchemaError("{} must be an array".format(label))
    return value


def contained_path(root: Path, value: str, label: str, must_exist: bool = False) -> Path:
    """Resolve a relative path and reject absolute paths and traversal."""
    _require_string(value, label)
    candidate = Path(value)
    if candidate.is_absolute():
        raise EvalSchemaError("{} must be relative: {}".format(label, value))
    root = Path(root).resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise EvalSchemaError("{} escapes its root: {}".format(label, value))
    if must_exist and not resolved.exists():
        raise EvalSchemaError("{} does not exist: {}".format(label, value))
    return resolved


def _check_keys(value: Dict[str, Any], allowed: set, label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise EvalSchemaError(
            "{} has unknown field(s): {}".format(label, ", ".join(sorted(unknown)))
        )


@dataclass(frozen=True)
class Expectation:
    kind: str
    data: Dict[str, Any]

    @classmethod
    def from_dict(cls, raw: Any, skill_root: Path, index: int) -> "Expectation":
        item = _require_mapping(raw, "expectations[{}]".format(index))
        if "kind" not in item:
            raise EvalSchemaError("expectations[{}].kind is required".format(index))
        kind = _require_string(item["kind"], "expectations[{}].kind".format(index))
        if kind not in EXPECTATION_KINDS:
            raise EvalSchemaError("unsupported expectation kind: {}".format(kind))

        common = {"kind"}
        if kind == "file_exists":
            _check_keys(item, common | {"path"}, "expectations[{}]".format(index))
            contained_path(Path(skill_root), item.get("path", ""), "file_exists.path")
            data = {"path": _require_string(item["path"], "file_exists.path")}
        elif kind in {"text_contains", "text_excludes", "regex"}:
            allowed = common | {"target", "value", "pattern"}
            _check_keys(item, allowed, "expectations[{}]".format(index))
            target = _require_string(item.get("target", ""), "{}.target".format(kind))
            if target not in {"final", "transcript"}:
                raise EvalSchemaError("{}.target must be final or transcript".format(kind))
            field = "pattern" if kind == "regex" else "value"
            value = _require_string(item.get(field, ""), "{}.{}".format(kind, field))
            if kind == "regex":
                try:
                    re.compile(value)
                except re.error as exc:
                    raise EvalSchemaError("invalid regex: {}".format(exc))
            data = {"target": target, field: value}
        elif kind == "json_value":
            _check_keys(item, common | {"path", "key", "equals"}, "expectations[{}]".format(index))
            contained_path(Path(skill_root), item.get("path", ""), "json_value.path")
            key = _require_string(item.get("key", ""), "json_value.key")
            if "equals" not in item:
                raise EvalSchemaError("json_value.equals is required")
            data = {"path": item["path"], "key": key, "equals": item["equals"]}
        elif kind == "validator":
            _check_keys(item, common | {"valid", "path"}, "expectations[{}]".format(index))
            valid = _require_bool(item.get("valid"), "validator.valid")
            path = item.get("path")
            if path is not None:
                contained_path(Path(skill_root), path, "validator.path")
            data = {"valid": valid}
            if path is not None:
                data["path"] = path
        elif kind == "command":
            _check_keys(item, common | {"argv", "exit_code", "timeout_seconds"}, "expectations[{}]".format(index))
            argv = _require_list(item.get("argv"), "command.argv")
            if not argv or not all(isinstance(arg, str) and arg for arg in argv):
                raise EvalSchemaError("command.argv must be a non-empty string array")
            exit_code = item.get("exit_code", 0)
            if not isinstance(exit_code, int) or isinstance(exit_code, bool):
                raise EvalSchemaError("command.exit_code must be an integer")
            timeout = item.get("timeout_seconds", 10)
            if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1 or timeout > 300:
                raise EvalSchemaError("command.timeout_seconds must be an integer from 1 to 300")
            data = {"argv": list(argv), "exit_code": exit_code, "timeout_seconds": timeout}
        else:  # judge
            _check_keys(item, common | {"rubric", "result"}, "expectations[{}]".format(index))
            rubric = _require_string(item.get("rubric", ""), "judge.rubric")
            contained_path(Path(skill_root), rubric, "judge.rubric", must_exist=True)
            result = _require_string(item.get("result", ""), "judge.result").lower()
            if result not in {"pass", "fail"}:
                raise EvalSchemaError("judge.result must be pass or fail")
            data = {"rubric": rubric, "result": result}
        return cls(kind, data)

    def as_dict(self) -> Dict[str, Any]:
        return dict({"kind": self.kind}, **self.data)


@dataclass(frozen=True)
class EvalCase:
    id: int
    name: str
    split: str
    prompt: str
    expected_output: str
    files: Tuple[str, ...]
    failure_modes: Tuple[str, ...]
    expectations: Tuple[Expectation, ...]

    @classmethod
    def from_dict(cls, raw: Any, skill_root: Path, index: int) -> "EvalCase":
        item = _require_mapping(raw, "evals[{}]".format(index))
        allowed = {
            "id", "name", "split", "prompt", "expected_output", "files",
            "failure_modes", "expectations",
        }
        _check_keys(item, allowed, "evals[{}]".format(index))
        case_id = item.get("id")
        if not isinstance(case_id, int) or isinstance(case_id, bool):
            raise EvalSchemaError("evals[{}].id must be an integer".format(index))
        name = _require_string(item.get("name"), "evals[{}].name".format(index))
        split = _require_string(item.get("split"), "evals[{}].split".format(index))
        if split not in SPLITS:
            raise EvalSchemaError("evals[{}].split must be train or held_out".format(index))
        prompt = _require_string(item.get("prompt"), "evals[{}].prompt".format(index))
        expected = _require_string(item.get("expected_output"), "evals[{}].expected_output".format(index))
        files = _require_list(item.get("files"), "evals[{}].files".format(index))
        clean_files = []
        for file_index, file_name in enumerate(files):
            file_name = _require_string(file_name, "evals[{}].files[{}]".format(index, file_index))
            contained_path(skill_root, file_name, "evals[{}].files[{}]".format(index, file_index), must_exist=True)
            clean_files.append(file_name)
        modes = _require_list(item.get("failure_modes"), "evals[{}].failure_modes".format(index))
        clean_modes = tuple(_require_string(mode, "failure_modes entry") for mode in modes)
        expectations = _require_list(item.get("expectations"), "evals[{}].expectations".format(index))
        if not expectations:
            raise EvalSchemaError("evals[{}].expectations must not be empty".format(index))
        parsed = tuple(
            Expectation.from_dict(value, skill_root, exp_index)
            for exp_index, value in enumerate(expectations)
        )
        return cls(case_id, name, split, prompt, expected, tuple(clean_files), clean_modes, parsed)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "split": self.split,
            "prompt": self.prompt,
            "expected_output": self.expected_output,
            "files": list(self.files),
            "failure_modes": list(self.failure_modes),
            "expectations": [item.as_dict() for item in self.expectations],
        }


@dataclass(frozen=True)
class EvalSuite:
    skill_name: str
    evals: Tuple[EvalCase, ...]
    version: int = EVAL_SCHEMA_VERSION

    def by_id(self, case_id: int) -> EvalCase:
        for case in self.evals:
            if case.id == case_id:
                return case
        raise EvalSchemaError("unknown eval id: {}".format(case_id))


def load_eval_suite(skill_root: Path) -> EvalSuite:
    skill_root = Path(skill_root).resolve()
    path = skill_root / "evals" / "evals.json"
    if not path.exists():
        raise EvalSchemaError("missing eval suite: {}".format(path))
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EvalSchemaError("cannot read {}: {}".format(path, exc))
    item = _require_mapping(raw, "evals.json")
    _check_keys(item, {"version", "skill_name", "evals"}, "evals.json")
    if item.get("version") != EVAL_SCHEMA_VERSION:
        raise EvalSchemaError("evals.json.version must be {}".format(EVAL_SCHEMA_VERSION))
    skill_name = _require_string(item.get("skill_name"), "skill_name")
    records = _require_list(item.get("evals"), "evals")
    if not records:
        raise EvalSchemaError("evals must not be empty")
    cases = tuple(EvalCase.from_dict(record, skill_root, index) for index, record in enumerate(records))
    ids = [case.id for case in cases]
    names = [case.name for case in cases]
    if len(ids) != len(set(ids)):
        raise EvalSchemaError("eval ids must be unique")
    if len(names) != len(set(names)):
        raise EvalSchemaError("eval names must be unique")
    return EvalSuite(skill_name, cases)


def load_trigger_queries(skill_root: Path) -> List[Dict[str, Any]]:
    path = Path(skill_root).resolve() / "evals" / "trigger_queries.json"
    if not path.exists():
        raise EvalSchemaError("missing trigger query file: {}".format(path))
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EvalSchemaError("cannot read {}: {}".format(path, exc))
    item = _require_mapping(raw, "trigger_queries.json")
    _check_keys(item, {"version", "queries"}, "trigger_queries.json")
    if item.get("version") != TRIGGER_SCHEMA_VERSION:
        raise EvalSchemaError("trigger_queries.json.version must be {}".format(TRIGGER_SCHEMA_VERSION))
    queries = _require_list(item.get("queries"), "trigger_queries.json.queries")
    result = []
    seen = set()
    for index, raw_query in enumerate(queries):
        query = _require_mapping(raw_query, "trigger query {}".format(index))
        _check_keys(query, {"query", "should_trigger", "split"}, "trigger query {}".format(index))
        text = _require_string(query.get("query"), "trigger query text")
        if text in seen:
            raise EvalSchemaError("duplicate trigger query: {}".format(text))
        seen.add(text)
        result.append({
            "query": text,
            "should_trigger": _require_bool(query.get("should_trigger"), "should_trigger"),
            "split": _require_string(query.get("split"), "split"),
        })
        if result[-1]["split"] not in SPLITS:
            raise EvalSchemaError("trigger query split must be train or held_out")
    if not result:
        raise EvalSchemaError("trigger queries must not be empty")
    return result


def load_judge_labels(skill_root: Path) -> Dict[str, Any]:
    path = Path(skill_root).resolve() / "evals" / "judge_labels.json"
    if not path.exists():
        return {"version": 1, "labels": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EvalSchemaError("cannot read {}: {}".format(path, exc))
    item = _require_mapping(raw, "judge_labels.json")
    _check_keys(item, {"version", "labels"}, "judge_labels.json")
    if item.get("version") != 1:
        raise EvalSchemaError("judge_labels.json.version must be 1")
    labels = _require_list(item.get("labels"), "judge_labels.json.labels")
    clean = []
    for index, label in enumerate(labels):
        label = _require_mapping(label, "judge label {}".format(index))
        _check_keys(label, {"rubric", "example", "result", "split"}, "judge label {}".format(index))
        rubric = _require_string(label.get("rubric"), "judge label rubric")
        contained_path(Path(skill_root), rubric, "judge label rubric", must_exist=True)
        result = _require_string(label.get("result"), "judge label result").lower()
        if result not in {"pass", "fail"}:
            raise EvalSchemaError("judge label result must be pass or fail")
        split = _require_string(label.get("split"), "judge label split")
        if split not in SPLITS:
            raise EvalSchemaError("judge label split must be train or held_out")
        _require_string(label.get("example"), "judge label example")
        clean.append(dict(label, result=result))
    return {"version": 1, "labels": clean}


def rubric_has_held_out_labels(skill_root: Path, rubric: str) -> bool:
    labels = load_judge_labels(skill_root)["labels"]
    return any(item["rubric"] == rubric and item["split"] == "held_out" for item in labels)
