#!/usr/bin/env python3
"""Deterministic skill-eval/v1 adapter used by integration tests and smoke."""
import json
import shutil
import sys
from pathlib import Path


def main():
    request = json.loads(sys.stdin.read())
    protocol = "skill-eval/v1"
    operation = request.get("operation")
    if operation == "revise":
        source = Path(request["skill_path"])
        destination = Path(request["candidate_path"])
        if destination.exists():
            shutil.rmtree(str(destination))
        shutil.copytree(str(source), str(destination))
        with (destination / "SKILL.md").open("a", encoding="utf-8") as handle:
            handle.write("\n# candidate-quality: high\n")
        print(json.dumps({"protocol": protocol, "status": "ok", "files": []}))
        return
    if operation == "judge":
        print(json.dumps({"protocol": protocol, "status": "ok", "result": "pass", "critique": "fixture"}))
        return
    if operation == "trigger":
        query = request.get("query", "").lower()
        triggered = any(word in query for word in ("skill", "evaluate", "workflow"))
        print(json.dumps({"protocol": protocol, "status": "ok", "triggered": triggered}))
        return
    if operation != "task":
        print(json.dumps({"protocol": protocol, "status": "error", "error": "unsupported operation"}))
        return
    output = Path(request["output_dir"])
    output.mkdir(parents=True, exist_ok=True)
    prompt = request.get("prompt", "")
    skill_path = request.get("skill_path")
    skill_text = ""
    if skill_path:
        skill_text = (Path(skill_path) / "SKILL.md").read_text(encoding="utf-8")
    high = "candidate-quality: high" in skill_text
    with_skill = bool(skill_path)
    if "held-out" in prompt:
        passed = with_skill and high
        final = "held-out-ok" if passed else "held-out-miss"
        result = "held-out-pass" if passed else "held-out-fail"
    else:
        passed = with_skill
        final = "trained" if passed else "baseline"
        result = "train-pass" if passed else "train-fail"
    (output / "report.json").write_text(json.dumps({"result": result}) + "\n", encoding="utf-8")
    print(json.dumps({
        "protocol": protocol,
        "status": "ok",
        "final": final,
        "transcript": "fixture adapter",
        "files": ["report.json"],
        "metrics": {"duration_ms": 1, "total_tokens": 10, "tool_calls": 1},
    }))


if __name__ == "__main__":
    main()
