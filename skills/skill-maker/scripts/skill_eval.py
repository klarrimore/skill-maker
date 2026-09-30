"""Audit, run, benchmark, and sandboxed-improve commands for Agent Skills."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from scripts.eval_adapter import AdapterError, CommandAdapter, PROTOCOL, error_response
from scripts.eval_models import (
    EvalCase,
    EvalSchemaError,
    EvalSuite,
    contained_path,
    load_eval_suite,
    load_judge_labels,
    load_trigger_queries,
    rubric_has_held_out_labels,
)
from scripts.eval_store import EvidenceStore
from scripts.quick_validate import ALLOWED_PROPERTIES, body_warnings, name_violation, validate_skill
from scripts.utils import parse_frontmatter


class ConfigurationError(RuntimeError):
    """The command cannot safely start because configuration is invalid."""


class EvaluationFailure(RuntimeError):
    """The operation completed with failed checks or audit findings."""



def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finding(
    finding_id: str,
    severity: str,
    category: str,
    status: str,
    path: str,
    evidence: str,
    fix: str,
) -> Dict[str, Any]:
    return {
        "id": finding_id,
        "severity": severity,
        "category": category,
        "status": status,
        "path": path,
        "evidence": evidence,
        "fix": fix,
    }


def _frontmatter(skill_dir: Path) -> Dict[str, Any]:
    path = Path(skill_dir) / "SKILL.md"
    try:
        frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError("cannot parse {}: {}".format(path, exc))
    return frontmatter


def _audit_skill(skill_dir: Path) -> Dict[str, Any]:
    """Return a stable audit report without invoking any model or command."""
    skill_dir = Path(skill_dir).resolve()
    findings: List[Dict[str, Any]] = []
    try:
        frontmatter = _frontmatter(skill_dir)
    except ConfigurationError:
        frontmatter = {}
    valid, message = validate_skill(skill_dir)
    if not valid:
        lower = message.lower()
        if "unexpected key" in lower:
            category = "portability_lock"
        elif "angle bracket" in lower or "em dash" in lower:
            category = "skill_maker_hardening"
        else:
            category = "spec_violation"
        findings.append(_finding(
            "skill.validation", "error", category, "open", "SKILL.md", message,
            "Fix the reported SKILL.md constraint and run quick_validate again.",
        ))
    else:
        findings.append(_finding(
            "skill.validation", "info", "spec_conformance", "passed", "SKILL.md", message,
            "No action required.",
        ))
    for index, warning in enumerate(body_warnings(skill_dir)):
        category = "portability_lock" if "non-ASCII" in warning else "advisory"
        findings.append(_finding(
            "skill.warning.{}".format(index + 1), "warning", category, "open", "SKILL.md", warning,
            "Read the warning, weigh the compatibility tradeoff, and document the decision.",
        ))

    eval_path = skill_dir / "evals" / "evals.json"
    suite: Optional[EvalSuite] = None
    try:
        suite = load_eval_suite(skill_dir)
        front_name = str(frontmatter.get("name", ""))
        if suite.skill_name != front_name:
            findings.append(_finding(
                "eval.skill-name", "error", "skill_maker_hardening", "open", "evals/evals.json",
                "skill_name '{}' does not match SKILL.md name '{}'".format(suite.skill_name, front_name),
                "Set evals.json.skill_name to the target skill name.",
            ))
        splits = {case.split for case in suite.evals}
        for split in ("train", "held_out"):
            if split not in splits:
                findings.append(_finding(
                    "eval.coverage.{}".format(split), "error", "skill_maker_hardening", "open",
                    "evals/evals.json", "No {} task evals are defined.".format(split),
                    "Add at least one task eval to the {} split.".format(split),
                ))
        catalogue = skill_dir / "evals" / "failure-modes.md"
        catalogue_text = catalogue.read_text(encoding="utf-8") if catalogue.exists() else ""
        for case in suite.evals:
            for mode in case.failure_modes:
                if not re.match(r"^FM-\d+$", mode) or mode not in catalogue_text:
                    findings.append(_finding(
                        "eval.failure-mode.{}.{}".format(case.id, mode), "error", "skill_maker_hardening", "open",
                        "evals/evals.json", "{} maps to missing failure mode {}".format(case.name, mode),
                        "Add the mode to failure-modes.md or correct the mapping.",
                    ))
            for index, expectation in enumerate(case.expectations):
                if expectation.kind == "command":
                    findings.append(_finding(
                        "eval.command.{}.{}".format(case.id, index), "warning", "skill_maker_hardening", "open",
                        "evals/evals.json", "Command expectation is disabled by default.",
                        "Use --allow-command-checks only after reviewing the literal argv and workspace boundary.",
                    ))
                if expectation.kind == "judge" and not rubric_has_held_out_labels(skill_dir, expectation.data["rubric"]):
                    findings.append(_finding(
                        "eval.judge-calibration.{}.{}".format(case.id, index), "warning", "advisory", "open",
                        "evals/evals.json", "Rubric has no held-out human label: {}".format(expectation.data["rubric"]),
                        "Add held-out labels to evals/judge_labels.json before using judge results as a benchmark gate.",
                    ))
                if expectation.kind == "judge":
                    rubric_text = contained_path(skill_dir, expectation.data["rubric"], "judge rubric", must_exist=True).read_text(encoding="utf-8").lower()
                    if re.search(r"file_exists|json_value|exit code|path must exist|validator", rubric_text):
                        findings.append(_finding(
                            "eval.objective-judge.{}.{}".format(case.id, index), "warning", "skill_maker_hardening", "open",
                            "evals/evals.json", "Judge rubric appears to delegate a deterministic artifact check.",
                            "Replace the judge with a local typed expectation such as file_exists, json_value, regex, or validator.",
                        ))
        if not catalogue.exists() or not catalogue_text.strip():
            findings.append(_finding(
                "eval.error-analysis", "warning", "advisory", "open", "evals/failure-modes.md",
                "No recorded failure-mode catalogue was found.",
                "Record observed and hypothesized failure modes and map each eval to them.",
            ))
    except EvalSchemaError as exc:
        findings.append(_finding(
            "eval.schema", "error", "skill_maker_hardening", "open", "evals/evals.json", str(exc),
            "Fix the versioned evaluation contract before running an adapter.",
        ))

    try:
        queries = load_trigger_queries(skill_dir)
        for split in ("train", "held_out"):
            subset = [item for item in queries if item["split"] == split]
            if not subset:
                findings.append(_finding(
                    "trigger.coverage.{}".format(split), "error", "skill_maker_hardening", "open",
                    "evals/trigger_queries.json", "No {} trigger queries are defined.".format(split),
                    "Add both positive and negative queries to the {} split.".format(split),
                ))
            elif not any(item["should_trigger"] for item in subset) or not any(not item["should_trigger"] for item in subset):
                findings.append(_finding(
                    "trigger.balance.{}".format(split), "error", "skill_maker_hardening", "open",
                    "evals/trigger_queries.json", "{} must contain both trigger labels.".format(split),
                    "Include should-trigger and near-miss should-not-trigger examples.",
                ))
        description = str(frontmatter.get("description", "")).lower()
        negative = [item["query"].lower() for item in queries if not item["should_trigger"]]
        if negative and not any(any(word in description for word in re.findall(r"[a-z]{5,}", query)) for query in negative):
            findings.append(_finding(
                "trigger.near-miss", "warning", "advisory", "open", "evals/trigger_queries.json",
                "Negative trigger queries share no recognizable terms with the description.",
                "Add domain-adjacent near misses so false positives are measured.",
            ))
    except EvalSchemaError as exc:
        findings.append(_finding(
            "trigger.schema", "error", "skill_maker_hardening", "open", "evals/trigger_queries.json", str(exc),
            "Fix the versioned trigger-query contract.",
        ))

    try:
        labels = load_judge_labels(skill_dir)["labels"]
        if labels and not any(item["split"] == "held_out" for item in labels):
            findings.append(_finding(
                "judge.held-out", "warning", "advisory", "open", "evals/judge_labels.json",
                "Judge labels exist but none are held out.",
                "Reserve labels unseen by revisions for calibration.",
            ))
    except EvalSchemaError as exc:
        findings.append(_finding(
            "judge.schema", "error", "skill_maker_hardening", "open", "evals/judge_labels.json", str(exc),
            "Fix the judge-label contract.",
        ))

    errors = sum(1 for item in findings if item["severity"] == "error" and item["status"] == "open")
    warnings = sum(1 for item in findings if item["severity"] == "warning" and item["status"] == "open")
    return {
        "protocol": PROTOCOL,
        "generated_at": _utc_now(),
        "skill_path": str(skill_dir),
        "skill_name": str(frontmatter.get("name", skill_dir.name)),
        "passed": errors == 0,
        "summary": {"errors": errors, "warnings": warnings, "findings": len(findings)},
        "findings": findings,
    }


def audit_skill(skill_dir: Path, workspace: Path) -> Dict[str, Any]:
    report = _audit_skill(Path(skill_dir))
    store = EvidenceStore(Path(workspace), session_id="audit-{}".format(uuid.uuid4().hex[:12]))
    path = store.write_json("audit.json", report)
    report["artifact"] = str(path)
    store.append_audit("audit", "audit", "offline", True, "allow", "local-audit", "passed" if report["passed"] else "failed", [path])
    return report


def _target_text(response: Dict[str, Any], target: str) -> str:
    value = response.get(target, "")
    if isinstance(value, list):
        return "\n".join(json.dumps(item, sort_keys=True) if not isinstance(item, str) else item for item in value)
    return str(value)


def _output_file(output_dir: Path, rel: str) -> Path:
    candidate = contained_path(output_dir, rel, "output path")
    return candidate


def _check(text: str, passed: bool, evidence: str, kind: str, calibrated: Optional[bool] = None) -> Dict[str, Any]:
    result = {"text": text, "passed": bool(passed), "evidence": evidence, "kind": kind}
    if calibrated is not None:
        result["calibrated"] = calibrated
    return result


def grade_artifact(skill_dir: Path) -> List[Dict[str, Any]]:
    """Grade the portable artifact checks used by the legacy self-eval wrapper."""
    skill_dir = Path(skill_dir).resolve()
    results: List[Dict[str, Any]] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [{"text": "Produces a skill directory containing a SKILL.md file", "passed": False, "evidence": "No SKILL.md at {}".format(skill_md)}]
    results.append({"text": "Produces a skill directory containing a SKILL.md file", "passed": True, "evidence": str(skill_md)})
    try:
        frontmatter, _body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except ValueError as exc:
        results.append({"text": "Frontmatter parses as YAML", "passed": False, "evidence": str(exc)})
        return results
    results.append({"text": "Frontmatter parses as YAML", "passed": True, "evidence": "parse_frontmatter succeeded"})
    name = str(frontmatter.get("name", "")).strip()
    results.append({
        "text": "Frontmatter name is kebab-case with no leading/trailing/consecutive hyphen",
        "passed": bool(name) and name_violation(name) is None,
        "evidence": "name={!r}".format(name),
    })
    results.append({
        "text": "Frontmatter name matches the skill directory name",
        "passed": name == skill_dir.name,
        "evidence": "name={!r}, dir={!r}".format(name, skill_dir.name),
    })
    description = str(frontmatter.get("description", "")).strip()
    results.append({
        "text": "Description is 1024 characters or fewer",
        "passed": bool(description) and len(description) <= 1024,
        "evidence": "length={}".format(len(description)) if description else "missing description",
    })
    clean_description = bool(description) and "<" not in description and ">" not in description
    results.append({
        "text": "Description contains no angle brackets (skill-maker hardening)",
        "passed": clean_description,
        "evidence": "clean" if clean_description else ("missing description" if not description else "contains angle brackets: {!r}".format(description)),
    })
    extra = sorted(set(frontmatter.keys()) - ALLOWED_PROPERTIES)
    results.append({
        "text": "Frontmatter uses only recognized fields (client extensions are spec-conformant but non-portable)",
        "passed": not extra,
        "evidence": "unexpected={}".format(extra) if extra else "no extra fields",
    })
    valid, message = validate_skill(skill_dir)
    results.append({"text": "Bundled validator reports the skill as valid", "passed": valid, "evidence": message})
    over_budget = [warning for warning in body_warnings(skill_dir) if "lines" in warning]
    results.append({
        "text": "SKILL.md body is under the 500-line budget",
        "passed": not over_budget,
        "evidence": over_budget[0] if over_budget else "under budget",
    })
    raw_text = skill_md.read_text(encoding="utf-8")
    results.append({
        "text": "SKILL.md contains no em dash (U+2014) in frontmatter or body",
        "passed": "—" not in raw_text,
        "evidence": "clean" if "—" not in raw_text else "em dash (U+2014) found in SKILL.md",
    })
    return results


def grade_expectation(
    expectation: Any,
    response: Dict[str, Any],
    output_dir: Path,
    skill_dir: Path,
    allow_command_checks: bool,
    store: EvidenceStore,
    run_id: str,
    expectation_index: int,
) -> Dict[str, Any]:
    kind = expectation.kind
    data = expectation.data
    label = "{}: {}".format(kind, json.dumps(data, sort_keys=True))
    if response.get("status") != "ok":
        return _check(label, False, response.get("error", "adapter failed"), kind)
    if kind == "file_exists":
        path = _output_file(output_dir, data["path"])
        return _check(label, path.is_file(), "{} exists".format(path) if path.is_file() else "{} is missing".format(path), kind)
    if kind in {"text_contains", "text_excludes", "regex"}:
        actual = _target_text(response, data["target"])
        if kind == "text_contains":
            passed = data["value"] in actual
            evidence = "literal found" if passed else "literal not found"
        elif kind == "text_excludes":
            passed = data["value"] not in actual
            evidence = "literal absent" if passed else "literal unexpectedly found"
        else:
            passed = re.search(data["pattern"], actual) is not None
            evidence = "pattern matched" if passed else "pattern did not match"
        return _check(label, passed, evidence, kind)
    if kind == "json_value":
        path = _output_file(output_dir, data["path"])
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            for part in data["key"].split("."):
                value = value[int(part)] if isinstance(value, list) else value[part]
            passed = value == data["equals"]
            evidence = "actual value: {}".format(json.dumps(value, sort_keys=True))
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            passed = False
            evidence = "could not read value: {}".format(exc)
        return _check(label, passed, evidence, kind)
    if kind == "validator":
        target = skill_dir if "path" not in data else contained_path(skill_dir, data["path"], "validator.path")
        actual, message = validate_skill(target)
        return _check(label, actual == data["valid"], message, kind)
    if kind == "command":
        if not allow_command_checks:
            store.append_audit("command", run_id, "local-command", False, "deny", "command-checks-disabled", "denied", [])
            return _check(label, False, "command checks are denied by default", kind)
        try:
            environment = {"PATH": os.environ.get("PATH", "")}
            completed = subprocess.run(
                data["argv"], cwd=str(output_dir), env=environment, shell=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=data["timeout_seconds"],
            )
            passed = completed.returncode == data["exit_code"]
            evidence = "exit code {}".format(completed.returncode)
            status = "passed" if passed else "failed"
        except (OSError, subprocess.TimeoutExpired) as exc:
            passed = False
            evidence = "command failed: {}".format(exc)
            status = "failed"
        store.append_audit("command", run_id, "local-command", True, "allow", "command-checks-enabled", status, [])
        return _check(label, passed, evidence, kind)
    # Judge results are supplied by a separate adapter operation.
    judge_results = response.get("judge_results", [])
    item = judge_results[expectation_index] if expectation_index < len(judge_results) else {}
    actual = str(item.get("result", "")).lower()
    passed = actual == data["result"]
    calibrated = rubric_has_held_out_labels(skill_dir, data["rubric"])
    return _check(label, passed, "judge result: {}".format(actual or "missing"), kind, calibrated)


def _copy_inputs(skill_dir: Path, case: EvalCase, run_dir: Path) -> List[str]:
    paths = []
    for rel in case.files:
        source = contained_path(skill_dir, rel, "eval input", must_exist=True)
        destination = contained_path(run_dir / "inputs", rel, "run input")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(str(source), str(destination), dirs_exist_ok=True)
        else:
            shutil.copy2(str(source), str(destination))
        paths.append(str(destination))
    return paths


def _request_for_task(skill_dir: Path, case: EvalCase, configuration: str, run_id: str, output_dir: Path, input_files: List[str]) -> Dict[str, Any]:
    return {
        "protocol": PROTOCOL,
        "operation": "task",
        "run_id": run_id,
        "skill_path": str(skill_dir) if configuration == "with_skill" else None,
        "configuration": configuration,
        "prompt": case.prompt,
        "expected_output": case.expected_output,
        "input_files": input_files,
        "output_dir": str(output_dir),
    }


def _run_case(
    skill_dir: Path,
    case: EvalCase,
    configuration: str,
    run_number: int,
    workspace: Path,
    adapter: CommandAdapter,
    allow_command_checks: bool,
) -> Dict[str, Any]:
    run_id = "{}-{}-{}".format(case.id, configuration, run_number)
    store = EvidenceStore(workspace)
    run_dir = store.run_dir(run_id)
    output_dir = contained_path(run_dir, "outputs", "output directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    input_files = _copy_inputs(skill_dir, case, run_dir)
    request = _request_for_task(skill_dir, case, configuration, run_id, output_dir, input_files)
    started = time.monotonic()
    try:
        adapter_result = adapter.run(request)
        response = adapter_result.response
        response.setdefault("metrics", {})
        response["metrics"].setdefault("duration_ms", int((time.monotonic() - started) * 1000))
        response["metrics"].setdefault("total_tokens", None)
        response["metrics"].setdefault("tool_calls", None)
        store.append_audit("task", run_id, adapter.executable, True, "allow", "adapter-configured", "passed", [run_dir])
    except AdapterError as exc:
        response = error_response(str(exc))
        response["metrics"] = {"duration_ms": int((time.monotonic() - started) * 1000), "total_tokens": None, "tool_calls": None}
        store.append_audit("task", run_id, adapter.executable, True, "allow", "adapter-configured", "failed", [run_dir])

    judge_results = []
    for index, expectation in enumerate(case.expectations):
        if expectation.kind != "judge" or response.get("status") != "ok":
            judge_results.append({})
            continue
        rubric_path = contained_path(skill_dir, expectation.data["rubric"], "judge rubric", must_exist=True)
        judge_request = {
            "protocol": PROTOCOL,
            "operation": "judge",
            "run_id": "{}-judge-{}".format(run_id, index),
            "skill_path": str(skill_dir) if configuration == "with_skill" else None,
            "prompt": _target_text(response, "final"),
            "transcript": response.get("transcript", ""),
            "rubric": str(rubric_path),
            "output_dir": str(output_dir),
        }
        try:
            judged = adapter.run(judge_request).response
            judge_results.append(judged)
            store.append_audit("judge", judge_request["run_id"], adapter.executable, True, "allow", "judge-request", judged.get("status", "error"), [run_dir])
        except AdapterError as exc:
            judge_results.append({"status": "error", "error": str(exc)})
            store.append_audit("judge", judge_request["run_id"], adapter.executable, True, "allow", "judge-request", "failed", [run_dir])
    response["judge_results"] = judge_results
    results = [
        grade_expectation(expectation, response, output_dir, skill_dir, allow_command_checks, store, run_id, index)
        for index, expectation in enumerate(case.expectations)
    ]
    passed = sum(1 for item in results if item["passed"])
    grading = {
        "protocol": PROTOCOL,
        "eval_id": case.id,
        "eval_name": case.name,
        "split": case.split,
        "configuration": configuration,
        "run_number": run_number,
        "status": "passed" if passed == len(results) else "failed",
        "expectations": results,
        "summary": {"passed": passed, "failed": len(results) - passed, "total": len(results), "pass_rate": passed / float(len(results))},
        "metrics": response.get("metrics", {}),
        "adapter_error": response.get("error") if response.get("status") == "error" else None,
        "artifacts": response.get("files", []),
    }
    store.write_run(run_id, request, response, grading)
    return grading


def execute_cases(
    skill_dir: Path,
    suite: EvalSuite,
    workspace: Path,
    adapter: CommandAdapter,
    runs: int,
    selected_cases: Sequence[EvalCase],
    allow_command_checks: bool = False,
) -> List[Dict[str, Any]]:
    if runs < 1:
        raise ConfigurationError("runs must be at least 1")
    results = []
    for run_number in range(1, runs + 1):
        for case in selected_cases:
            for configuration in ("with_skill", "without_skill"):
                results.append(_run_case(Path(skill_dir).resolve(), case, configuration, run_number, Path(workspace).resolve(), adapter, allow_command_checks))
    return results


def _mean(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def _stddev(values: List[float]) -> Optional[float]:
    if not values:
        return None
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    pass_rates = [float(row["summary"]["pass_rate"]) for row in rows]
    durations = [row.get("metrics", {}).get("duration_ms") for row in rows if isinstance(row.get("metrics", {}).get("duration_ms"), (int, float))]
    tokens = [row.get("metrics", {}).get("total_tokens") for row in rows if isinstance(row.get("metrics", {}).get("total_tokens"), (int, float))]
    objective_rates = []
    judge_rates = []
    for row in rows:
        objective = [item for item in row.get("expectations", []) if item.get("kind") != "judge"]
        judges = [item for item in row.get("expectations", []) if item.get("kind") == "judge" and item.get("calibrated")]
        if objective:
            objective_rates.append(sum(1 for item in objective if item.get("passed")) / float(len(objective)))
        if judges:
            judge_rates.append(sum(1 for item in judges if item.get("passed")) / float(len(judges)))
    def metric(values: List[float]) -> Dict[str, Any]:
        return {"mean": _mean(values), "stddev": _stddev(values), "min": min(values) if values else None, "max": max(values) if values else None}
    return {
        "pass_rate": metric(pass_rates),
        "objective_pass_rate": metric(objective_rates),
        "calibrated_judge_pass_rate": metric(judge_rates),
        "time_seconds": metric([value / 1000.0 for value in durations]),
        "tokens": metric([float(value) for value in tokens]),
        "runs": len(rows),
        "missing_metrics": {"duration_ms": len(rows) - len(durations), "total_tokens": len(rows) - len(tokens)},
    }


def benchmark_records(rows: List[Dict[str, Any]], skill_dir: Path, workspace: Path) -> Dict[str, Any]:
    if not rows:
        raise ConfigurationError("no grading records found")
    keys = {(row.get("eval_id"), row.get("run_number")) for row in rows}
    for key in keys:
        configs = {row.get("configuration") for row in rows if (row.get("eval_id"), row.get("run_number")) == key}
        if configs != {"with_skill", "without_skill"}:
            raise ConfigurationError("incomplete paired run for eval {} run {}".format(*key))
    configurations = {}
    for configuration in ("with_skill", "without_skill"):
        configurations[configuration] = _stats([row for row in rows if row.get("configuration") == configuration])
    with_rate = configurations["with_skill"]["pass_rate"]["mean"]
    without_rate = configurations["without_skill"]["pass_rate"]["mean"]
    diagnostics = []
    for row in rows:
        if row.get("adapter_error"):
            diagnostics.append({"severity": "error", "code": "adapter_failure", "eval_id": row.get("eval_id"), "evidence": row["adapter_error"]})
        if any(item.get("kind") == "judge" and not item.get("calibrated", False) for item in row.get("expectations", [])):
            diagnostics.append({"severity": "warning", "code": "uncalibrated_judge", "eval_id": row.get("eval_id"), "evidence": "judge result excluded from objective gate"})
    for config, summary in configurations.items():
        if summary["pass_rate"]["stddev"] is not None and summary["pass_rate"]["stddev"] > 0.25:
            diagnostics.append({"severity": "warning", "code": "high_variance", "configuration": config, "evidence": summary["pass_rate"]["stddev"]})
        if summary["missing_metrics"]["duration_ms"] or summary["missing_metrics"]["total_tokens"]:
            diagnostics.append({"severity": "warning", "code": "missing_metrics", "configuration": config, "evidence": summary["missing_metrics"]})
    if with_rate is not None and without_rate is not None and with_rate <= without_rate:
        diagnostics.append({"severity": "warning", "code": "no_quality_gain", "evidence": "with_skill does not beat baseline"})
    with_tokens = configurations["with_skill"]["tokens"]["mean"]
    without_tokens = configurations["without_skill"]["tokens"]["mean"]
    if with_tokens is not None and without_tokens is not None and with_tokens > without_tokens and (with_rate or 0) <= (without_rate or 0):
        diagnostics.append({"severity": "warning", "code": "cost_grows_without_gain", "evidence": "token mean increased without a pass-rate gain"})
    benchmark_runs = []
    for row in rows:
        item = dict(row)
        metrics = row.get("metrics", {})
        item["result"] = {
            "pass_rate": row.get("summary", {}).get("pass_rate"),
            "passed": row.get("summary", {}).get("passed"),
            "failed": row.get("summary", {}).get("failed"),
            "total": row.get("summary", {}).get("total"),
            "time_seconds": metrics.get("duration_ms") / 1000.0 if isinstance(metrics.get("duration_ms"), (int, float)) else None,
            "tokens": metrics.get("total_tokens"),
            "tool_calls": metrics.get("tool_calls"),
            "errors": 1 if row.get("adapter_error") else 0,
        }
        benchmark_runs.append(item)
    report = {
        "protocol": PROTOCOL,
        "metadata": {
            "skill_name": _frontmatter(skill_dir).get("name", Path(skill_dir).name),
            "skill_path": str(Path(skill_dir).resolve()),
            "timestamp": _utc_now(),
            "runs_per_configuration": len({row.get("run_number") for row in rows}),
            "evals_run": sorted({row.get("eval_id") for row in rows}),
        },
        "runs": benchmark_runs,
        "configurations": configurations,
        "run_summary": {
            "with_skill": configurations["with_skill"],
            "without_skill": configurations["without_skill"],
            "delta": {
                "pass_rate": (with_rate - without_rate) if with_rate is not None and without_rate is not None else None,
                "time_seconds": (configurations["with_skill"]["time_seconds"]["mean"] - configurations["without_skill"]["time_seconds"]["mean"]) if configurations["with_skill"]["time_seconds"]["mean"] is not None and configurations["without_skill"]["time_seconds"]["mean"] is not None else None,
                "tokens": (with_tokens - without_tokens) if with_tokens is not None and without_tokens is not None else None,
            },
        },
        "deltas": {
            "pass_rate": (with_rate - without_rate) if with_rate is not None and without_rate is not None else None,
            "time_seconds": (configurations["with_skill"]["time_seconds"]["mean"] - configurations["without_skill"]["time_seconds"]["mean"]) if configurations["with_skill"]["time_seconds"]["mean"] is not None and configurations["without_skill"]["time_seconds"]["mean"] is not None else None,
            "tokens": (with_tokens - without_tokens) if with_tokens is not None and without_tokens is not None else None,
        },
        "diagnostics": diagnostics,
        "notes": ["Objective checks and calibrated judge checks are reported separately in grading records."],
    }
    store = EvidenceStore(workspace)
    json_path = store.write_json("benchmark.json", report)
    markdown = ["# Benchmark", "", "- Skill: `{}`".format(report["metadata"]["skill_name"]), "- Runs per configuration: {}".format(report["metadata"]["runs_per_configuration"]), "", "| Configuration | Pass rate mean | Time mean (s) | Tokens mean |", "| --- | ---: | ---: | ---: |"]
    for config in ("with_skill", "without_skill"):
        summary = configurations[config]
        markdown.append("| {} | {} | {} | {} |".format(config, summary["pass_rate"]["mean"], summary["time_seconds"]["mean"], summary["tokens"]["mean"]))
    if diagnostics:
        markdown.extend(["", "## Diagnostics"])
        markdown.extend("- `{}`: {}".format(item["code"], item["evidence"]) for item in diagnostics)
    (Path(workspace) / "benchmark.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    store.append_audit("benchmark", "benchmark", "offline", True, "allow", "record-aggregation", "passed", [json_path, Path(workspace) / "benchmark.md"])
    report["artifacts"] = [str(json_path), str(Path(workspace) / "benchmark.md")]
    return report


def benchmark_skill(skill_dir: Path, workspace: Path) -> Dict[str, Any]:
    paths = sorted(Path(workspace).resolve().rglob("grading.json"))
    rows = []
    for path in paths:
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigurationError("invalid grading record {}: {}".format(path, exc))
        if row.get("operation") == "trigger":
            continue
        if row.get("protocol") != PROTOCOL:
            raise ConfigurationError("mixed or missing protocol in {}".format(path))
        rows.append(row)
    return benchmark_records(rows, Path(skill_dir).resolve(), Path(workspace).resolve())


def _score(rows: List[Dict[str, Any]], split: str) -> Tuple[float, float, float, float]:
    candidates = [row for row in rows if row.get("configuration") == "with_skill" and row.get("split") == split]
    objective_rates = []
    for row in candidates:
        objective = [item for item in row.get("expectations", []) if item.get("kind") != "judge"]
        if objective:
            objective_rates.append(sum(1 for item in objective if item.get("passed")) / float(len(objective)))
    objective = _mean(objective_rates) or 0.0
    judge_items = [item for row in candidates for item in row.get("expectations", []) if item.get("kind") == "judge" and item.get("calibrated")]
    judge_rate = _mean([1.0 if item["passed"] else 0.0 for item in judge_items]) or 0.0
    token_values = [row.get("metrics", {}).get("total_tokens") for row in candidates if isinstance(row.get("metrics", {}).get("total_tokens"), (int, float))]
    duration_values = [row.get("metrics", {}).get("duration_ms") for row in candidates if isinstance(row.get("metrics", {}).get("duration_ms"), (int, float))]
    return objective, judge_rate, -(_mean([float(item) for item in token_values]) or 0.0), -(_mean([float(item) for item in duration_values]) or 0.0)


def _revision_packet(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    packet = []
    for row in rows:
        if row.get("configuration") != "with_skill" or row.get("split") != "train":
            continue
        failures = [item for item in row.get("expectations", []) if not item.get("passed")]
        if failures:
            packet.append({
                "eval_id": row.get("eval_id"),
                "expectations": [{"text": item.get("text"), "evidence": item.get("evidence")} for item in failures],
                "artifacts": row.get("artifacts", []),
            })
    return packet
def execute_triggers(skill_dir: Path, workspace: Path, adapter: CommandAdapter, runs: int = 3) -> Dict[str, Any]:
    if runs < 3:
        raise ConfigurationError("trigger evaluation requires at least 3 runs per query")
    queries = load_trigger_queries(skill_dir)
    description = _frontmatter(skill_dir).get("description", "")
    store = EvidenceStore(workspace)
    records = []
    for index, query in enumerate(queries):
        triggered = []
        for run_number in range(1, runs + 1):
            run_id = "trigger-{}-{}".format(index, run_number)
            run_dir = store.run_dir(run_id)
            output_dir = run_dir / "outputs"
            output_dir.mkdir(parents=True, exist_ok=True)
            request = {
                "protocol": PROTOCOL, "operation": "trigger", "run_id": run_id,
                "skill_path": str(Path(skill_dir).resolve()), "description": description,
                "query": query["query"], "should_trigger": query["should_trigger"],
                "output_dir": str(output_dir),
            }
            try:
                response = adapter.run(request).response
                value = bool(response.get("triggered", False)) if response.get("status") == "ok" else False
                status = "passed" if response.get("status") == "ok" else "failed"
            except AdapterError as exc:
                response = error_response(str(exc))
                value = False
                status = "failed"
            triggered.append(value)
            store.write_run(run_id, request, response, {
                "protocol": PROTOCOL, "operation": "trigger", "query": query["query"],
                "split": query["split"], "should_trigger": query["should_trigger"],
                "triggered": value, "status": status,
            })
            store.append_audit("trigger", run_id, adapter.executable, True, "allow", "adapter-configured", status, [run_dir])
        rate = sum(1 for value in triggered if value) / float(runs)
        records.append(dict(query, trigger_rate=rate, passed=(rate >= 0.5) == query["should_trigger"]))
    scores = {}
    for split in ("train", "held_out"):
        subset = [item for item in records if item["split"] == split]
        scores[split] = sum(1 for item in subset if item["passed"]) / float(len(subset)) if subset else 0.0
    report = {
        "protocol": PROTOCOL, "skill_name": _frontmatter(skill_dir).get("name", Path(skill_dir).name),
        "description": description, "runs_per_query": runs, "threshold": 0.5,
        "runs": records, "scores": scores, "selected": "current",
    }
    store.write_json("trigger_results.json", report)
    return report




def improve_skill(
    skill_dir: Path,
    workspace: Path,
    adapter: CommandAdapter,
    runs: int,
    max_iterations: int,
    allow_command_checks: bool = False,
) -> Dict[str, Any]:
    skill_dir = Path(skill_dir).resolve()
    workspace = Path(workspace).resolve()
    source_audit = _audit_skill(skill_dir)
    if not source_audit["passed"]:
        raise EvaluationFailure("source audit has errors")
    suite = load_eval_suite(skill_dir)
    if not any(case.split == "train" for case in suite.evals) or not any(case.split == "held_out" for case in suite.evals):
        raise ConfigurationError("improvement requires train and held_out cases")
    workspace.mkdir(parents=True, exist_ok=True)
    candidates = workspace / "candidates"
    candidates.mkdir(exist_ok=True)
    v0_container = candidates / "v0"
    if v0_container.exists():
        shutil.rmtree(str(v0_container))
    v0 = v0_container / suite.skill_name
    v0_container.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(skill_dir), str(v0))
    history = {"protocol": PROTOCOL, "started_at": _utc_now(), "skill_name": suite.skill_name, "current_best": "v0", "iterations": []}
    version_rows: Dict[str, List[Dict[str, Any]]] = {}
    current = v0
    current_version = "v0"

    def evaluate(version: str, path: Path) -> List[Dict[str, Any]]:
        iteration_workspace = workspace / "iterations" / version
        if iteration_workspace.exists():
            shutil.rmtree(str(iteration_workspace))
        iteration_workspace.mkdir(parents=True)
        rows = execute_cases(path, suite, iteration_workspace, adapter, runs, list(suite.evals), allow_command_checks)
        version_rows[version] = rows
        return rows

    current_rows = evaluate("v0", current)
    history["iterations"].append({
        "version": "v0", "parent": None, "train_score": _score(current_rows, "train"), "held_out_score": _score(current_rows, "held_out"),
        "validation": {"valid": True}, "audit": source_audit, "grading_result": "baseline", "is_current_best": True,
    })
    for iteration in range(1, max_iterations + 1):
        packet = _revision_packet(current_rows)
        version = "v{}".format(iteration)
        candidate_container = candidates / version
        if candidate_container.exists():
            shutil.rmtree(str(candidate_container))
        candidate = candidate_container / suite.skill_name
        candidate_container.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(current), str(candidate))
        revise_dir = workspace / "iterations" / version / "revision"
        revise_dir.mkdir(parents=True, exist_ok=True)
        request = {
            "protocol": PROTOCOL,
            "operation": "revise",
            "run_id": "{}-revise".format(version),
            "skill_path": str(current),
            "candidate_path": str(candidate),
            "training_failures": packet,
            "output_dir": str(revise_dir),
        }
        try:
            revision = adapter.run(request).response
            revision_error = None if revision.get("status") == "ok" else revision.get("error", "revision failed")
        except AdapterError as exc:
            revision = error_response(str(exc))
            revision_error = str(exc)
        EvidenceStore(workspace).append_audit("revise", request["run_id"], adapter.executable, True, "allow", "training-only-revision", "failed" if revision_error else "passed", [candidate])
        candidate_audit = _audit_skill(candidate) if not revision_error else {"passed": False, "summary": {"errors": 1}, "findings": [{"id": "revision.error", "severity": "error", "evidence": revision_error}]}
        if not candidate_audit["passed"]:
            history["iterations"].append({
                "version": version, "parent": current_version, "train_score": None, "held_out_score": None,
                "validation": {"valid": False, "error": revision_error}, "audit": candidate_audit,
                "grading_result": "invalid", "is_current_best": True,
            })
            break
        candidate_rows = evaluate(version, candidate)
        incumbent_score = _score(current_rows, "held_out")
        candidate_score = _score(candidate_rows, "held_out")
        if candidate_score > incumbent_score:
            result = "won"
            current = candidate
            current_version = version
            current_rows = candidate_rows
        elif candidate_score == incumbent_score:
            result = "tie"
        else:
            result = "lost"
        for previous in history["iterations"]:
            previous["is_current_best"] = previous["version"] == current_version
        history["iterations"].append({
            "version": version, "parent": history["iterations"][-1]["version"],
            "train_score": _score(candidate_rows, "train"), "held_out_score": candidate_score,
            "validation": {"valid": True}, "audit": candidate_audit, "grading_result": result,
            "is_current_best": result == "won",
        })
        if result != "won":
            break
    for item in history["iterations"]:
        item["is_current_best"] = item["version"] == current_version
    history["current_best"] = current_version
    # Keep the source skill's directory identity. ``best-skill`` is a
    # workspace container, and the validated artifact sits below it at the
    # original skill name rather than being renamed to the container name.
    best = workspace / "best-skill" / suite.skill_name
    if best.parent.exists():
        shutil.rmtree(str(best.parent))
    best.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(current), str(best))
    best_valid, best_message = validate_skill(best)
    if not best_valid:
        raise EvaluationFailure("promoted best skill failed validation: {}".format(best_message))
    history["best_skill"] = str(best)
    EvidenceStore(workspace).write_json("history.json", history)
    return history


def _adapter_from_args(args: argparse.Namespace) -> CommandAdapter:
    if not args.adapter_arg:
        raise ConfigurationError("model-backed commands require at least one --adapter-arg")
    return CommandAdapter(args.adapter_arg, timeout_seconds=args.timeout)


def _select_cases(suite: EvalSuite, eval_ids: Optional[List[int]], split: Optional[str]) -> List[EvalCase]:
    cases = list(suite.evals)
    if eval_ids:
        wanted = set(eval_ids)
        cases = [case for case in cases if case.id in wanted]
        if len(cases) != len(wanted):
            raise ConfigurationError("an --eval-id does not exist")
    if split:
        cases = [case for case in cases if case.split == split]
    if not cases:
        raise ConfigurationError("no eval cases selected")
    return cases


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("skill")
    audit.add_argument("--workspace", required=True)
    run = sub.add_parser("run")
    run.add_argument("skill")
    run.add_argument("--workspace", required=True)
    run.add_argument("--runs", type=int, default=1)
    run.add_argument("--eval-id", type=int, action="append")
    run.add_argument("--split", choices=["train", "held_out"])
    run.add_argument("--trigger", action="store_true")
    run.add_argument("--allow-command-checks", action="store_true")
    run.add_argument("--timeout", type=int, default=300)
    run.add_argument("--adapter-arg", action="append", default=[])
    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("skill")
    benchmark.add_argument("--workspace", required=True)
    improve = sub.add_parser("improve")
    improve.add_argument("skill")
    improve.add_argument("--workspace", required=True)
    improve.add_argument("--runs", type=int, default=1)
    improve.add_argument("--max-iterations", type=int, default=3)
    improve.add_argument("--allow-command-checks", action="store_true")
    improve.add_argument("--timeout", type=int, default=300)
    improve.add_argument("--adapter-arg", action="append", default=[])
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        skill_dir = Path(args.skill).resolve()
        if args.command == "audit":
            result = audit_skill(skill_dir, Path(args.workspace))
            print(json.dumps(result, sort_keys=True))
            return 0 if result["passed"] else 1
        if args.command == "run":
            report = audit_skill(skill_dir, Path(args.workspace))
            if not report["passed"]:
                print(json.dumps(report, sort_keys=True))
                return 1
            adapter = _adapter_from_args(args)
            if args.trigger:
                if args.eval_id or args.split:
                    raise ConfigurationError("--trigger cannot be combined with task eval filters")
                result = execute_triggers(skill_dir, Path(args.workspace), adapter, args.runs)
                print(json.dumps(result, sort_keys=True))
                return 0 if all(item["passed"] for item in result["runs"]) else 1
            suite = load_eval_suite(skill_dir)
            rows = execute_cases(skill_dir, suite, Path(args.workspace), adapter, args.runs, _select_cases(suite, args.eval_id, args.split), args.allow_command_checks)
            result = {"protocol": PROTOCOL, "status": "passed" if all(row["status"] == "passed" for row in rows) else "failed", "runs": rows}
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "passed" else 1
        if args.command == "benchmark":
            result = benchmark_skill(skill_dir, Path(args.workspace))
            print(json.dumps(result, sort_keys=True))
            return 0 if not any(item.get("severity") == "error" for item in result["diagnostics"]) else 1
        if args.command == "improve":
            result = improve_skill(skill_dir, Path(args.workspace), _adapter_from_args(args), args.runs, args.max_iterations, args.allow_command_checks)
            print(json.dumps(result, sort_keys=True))
            return 0
        raise ConfigurationError("unknown command")
    except EvaluationFailure as exc:
        print(json.dumps({"protocol": PROTOCOL, "status": "failed", "error": str(exc)}))
        return 1
    except (ConfigurationError, EvalSchemaError, ValueError, OSError) as exc:
        print(json.dumps({"protocol": PROTOCOL, "status": "configuration_error", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
