#!/usr/bin/env python3
"""
Quick validation script for skills - zero-network spec checker.

Fallback for the reference validator `skills-ref validate ./your-skill` (the standard's
reference/demonstration library, not a production SDK). Enforces the agentskills.io
frontmatter constraints and emits soft warnings on the SKILL.md body budget. As a
skill-maker hardening measure it also rejects angle brackets in the description and the
em dash character (U+2014) anywhere in the file; the spec is silent on both and
`skills-ref` does not check them.

Two modes:
  - strict (default): portable-spec validation used by package/install. Errors are
    portability violations; warnings are body-budget advisories.
  - import: read-only compatibility inspection for an existing client-specific skill.
    Only fatal structural issues (missing SKILL.md, bad YAML, missing/empty description)
    are errors; portability issues are warnings so the skill can be examined before
    conversion.

Exports:
  inspect_skill(skill_path, mode="strict") -> dict
  validate_skill(skill_path) -> (bool, message)   [strict wrapper for existing callers]
  body_warnings(skill_path) -> [str]
"""

import argparse
import json
import sys
import unicodedata
from pathlib import Path

from scripts.utils import parse_frontmatter

# Directories whose contents are not packaged as part of the skill, so any
# SKILL.md inside them shouldn't count toward the single-SKILL.md check below.
# Mirrors package_skill.py: __pycache__ and node_modules are excluded at any
# depth, while evals and tests are only excluded at the skill root.
EXCLUDED_DIR_PARTS = {'__pycache__', 'node_modules', '.pytest_cache'}
ROOT_EXCLUDED_DIR_PARTS = {'evals', 'tests'}

# Soft budget for the SKILL.md body (recommendation, not a hard limit, per the spec).
BODY_LINE_BUDGET = 500
BODY_TOKEN_BUDGET = 5000  # approximated as chars / 4
# Codex's MAX_SKILL_PROMPT_BYTES hard truncation cap (~2000 tokens) on a selected
# skill's body in its default configuration, as of 2026-09-30. Tighter than the
# open standard's own 5000-token recommendation above, so it gets its own warning.
BODY_BYTE_BUDGET_CODEX = 8000

# The six recognized agentskills.io frontmatter fields. Anything else is a
# client-specific extension: still spec-conformant, but it breaks portability.
ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}


def name_violation(name):
    """Return the first name-rule violation, or None if `name` is valid."""
    normalized = unicodedata.normalize('NFKC', name)
    if normalized != normalized.lower() or not all(
        ch.isalnum() or ch == '-' for ch in normalized
    ):
        return f"Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)"
    if normalized.startswith('-') or normalized.endswith('-') or '--' in normalized:
        return f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
    if len(normalized) > 64:
        return f"Name is too long ({len(normalized)} characters). Maximum is 64 characters."
    return None


def _counts_as_skill_md(rel_path):
    """True if a SKILL.md at rel_path (relative to the skill root) would be packaged."""
    dir_parts = rel_path.parts[:-1]
    if any(part in EXCLUDED_DIR_PARTS for part in dir_parts):
        return False
    if dir_parts and dir_parts[0] in ROOT_EXCLUDED_DIR_PARTS:
        return False
    return True


def inspect_skill(skill_path, mode="strict"):
    """Shared diagnostic engine for skill validation.

    Args:
        skill_path: Path to skill directory (string or Path).
        mode: "strict" for portable validation, "import" for compatibility inspection.

    Returns:
        dict: {"mode": mode, "valid": bool, "errors": [str], "warnings": [str]}
    """
    skill_path = Path(skill_path).resolve()
    if mode not in ("strict", "import"):
        return {"mode": mode, "valid": False, "errors": [f"Invalid mode '{mode}'. Must be 'strict' or 'import'."], "warnings": []}
    report = {"mode": mode, "valid": False, "errors": [], "warnings": []}

    # --- structural checks (both modes) ---

    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        report["errors"].append("SKILL.md not found")
        return report

    try:
        content = skill_md.read_text()
    except Exception as e:
        report["errors"].append(f"Cannot read SKILL.md: {e}")
        return report

    try:
        frontmatter, body = parse_frontmatter(content)
    except ValueError as e:
        report["errors"].append(str(e))
        return report

    # --- multiple SKILL.md check ---
    skill_md_files = [
        p for p in skill_path.rglob('SKILL.md')
        if _counts_as_skill_md(p.relative_to(skill_path))
    ]
    if len(skill_md_files) > 1:
        extras = sorted(
            str(p.relative_to(skill_path)) for p in skill_md_files
            if p.resolve() != skill_md.resolve()
        )
        msg = (
            f"Found {len(skill_md_files)} SKILL.md files, but a skill must contain "
            f"exactly one at <folder>/SKILL.md. Extra: {', '.join(extras)}."
        )
        if mode == "strict":
            report["errors"].append(msg)
        else:
            report["warnings"].append(msg)

    # --- name validation ---
    if 'name' not in frontmatter:
        name_err = "Missing 'name' in frontmatter"
        if mode == "strict":
            report["errors"].append(name_err)
        else:
            report["warnings"].append(name_err)
    elif not isinstance(frontmatter.get('name'), str):
        name_err = f"Name must be a string, got {type(frontmatter.get('name')).__name__}"
        if mode == "strict":
            report["errors"].append(name_err)
        else:
            report["warnings"].append(name_err)
    else:
        name = frontmatter.get('name', '').strip()
        if not name:
            name_err = "Name is empty or whitespace-only."
            if mode == "strict":
                report["errors"].append(name_err)
            else:
                report["warnings"].append(name_err)
        else:
            violation = name_violation(name)
            if violation:
                if mode == "strict":
                    report["errors"].append(violation)
                else:
                    report["warnings"].append(violation)

            # Name must match the parent directory name (spec requirement)
            dir_name = skill_path.name
            if dir_name and unicodedata.normalize('NFKC', name) != unicodedata.normalize('NFKC', dir_name):
                msg = f"Name '{name}' must match the parent directory name '{dir_name}'. Rename the directory or the 'name' field so they are identical."
                if mode == "strict":
                    report["errors"].append(msg)
                else:
                    report["warnings"].append(msg)

    # --- description validation ---
    if 'description' not in frontmatter:
        report["errors"].append("Missing 'description' in frontmatter")
    elif not isinstance(frontmatter.get('description'), str):
        report["errors"].append(f"Description must be a string, got {type(frontmatter.get('description')).__name__}")
    else:
        description = frontmatter.get('description', '').strip()
        if not description:
            report["errors"].append("Description must be non-empty.")
        else:
            if '<' in description or '>' in description:
                msg = "Description cannot contain angle brackets (< or >)"
                if mode == "strict":
                    report["errors"].append(msg)
                else:
                    report["warnings"].append(msg)
            if len(description) > 1024:
                report["errors"].append(
                    f"Description is too long ({len(description)} characters). Maximum is 1024 characters."
                )

    # --- em dash hardening ---
    if '—' in content:
        msg = "SKILL.md cannot contain the em dash character (U+2014). Use a comma, period, colon, or parentheses instead."
        if mode == "strict":
            report["errors"].append(msg)
        else:
            report["warnings"].append(msg)

    # --- unexpected top-level fields ---
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        msg = (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(map(str, unexpected_keys)))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}. "
            f"Fields outside the standard are spec-conformant but not portable; "
            f"put environment needs in 'compatibility'."
        )
        if mode == "strict":
            report["errors"].append(msg)
        else:
            report["warnings"].append(msg)

    # --- optional-field type/length violations ---
    if 'license' in frontmatter and not isinstance(frontmatter.get('license'), str):
        msg = f"License must be a string, got {type(frontmatter.get('license')).__name__}"
        if mode == "strict":
            report["errors"].append(msg)
        else:
            report["warnings"].append(msg)

    if 'allowed-tools' in frontmatter and not isinstance(frontmatter.get('allowed-tools'), str):
        msg = f"Allowed tools must be a string, got {type(frontmatter.get('allowed-tools')).__name__}"
        if mode == "strict":
            report["errors"].append(msg)
        else:
            report["warnings"].append(msg)

    if 'compatibility' in frontmatter:
        compatibility = frontmatter.get('compatibility')
        if not isinstance(compatibility, str):
            msg = f"Compatibility must be a string, got {type(compatibility).__name__}"
            if mode == "strict":
                report["errors"].append(msg)
            else:
                report["warnings"].append(msg)
        elif len(compatibility) > 500:
            msg = f"Compatibility is too long ({len(compatibility)} characters). Maximum is 500 characters."
            if mode == "strict":
                report["errors"].append(msg)
            else:
                report["warnings"].append(msg)

    if 'metadata' in frontmatter:
        metadata = frontmatter.get('metadata')
        if not isinstance(metadata, dict):
            msg = f"Metadata must be a mapping, got {type(metadata).__name__}"
            if mode == "strict":
                report["errors"].append(msg)
            else:
                report["warnings"].append(msg)
        else:
            if not all(isinstance(key, str) for key in metadata):
                msg = "Metadata keys must be strings"
                if mode == "strict":
                    report["errors"].append(msg)
                else:
                    report["warnings"].append(msg)
            if not all(isinstance(value, str) for value in metadata.values()):
                msg = "Metadata values must be strings"
                if mode == "strict":
                    report["errors"].append(msg)
                else:
                    report["warnings"].append(msg)

    # --- body budget warnings (always warnings) ---
    lines = body.count('\n') + 1
    approx_tokens = len(body) // 4
    body_bytes = len(body.encode('utf-8'))
    if lines > BODY_LINE_BUDGET:
        report["warnings"].append(
            f"SKILL.md body is {lines} lines (recommended under {BODY_LINE_BUDGET}). "
            f"Move detail into references/ and point to it."
        )
    if approx_tokens > BODY_TOKEN_BUDGET:
        report["warnings"].append(
            f"SKILL.md body is roughly {approx_tokens} tokens (recommended under "
            f"{BODY_TOKEN_BUDGET}). Move detail into references/ and point to it."
        )
    if body_bytes > BODY_BYTE_BUDGET_CODEX:
        report["warnings"].append(
            f"SKILL.md body is {body_bytes} bytes. Codex hard-truncates a selected "
            f"skill's body at about {BODY_BYTE_BUDGET_CODEX} bytes (~2000 tokens) by "
            f"default, well under the open standard's own 5000-token recommendation. "
            f"If you need Codex compatibility, trim well under this."
        )

    # Description ceiling advisory: within 5% of the 1024 limit is a maintenance trap.
    desc_val = frontmatter.get('description')
    desc = desc_val.strip() if isinstance(desc_val, str) else ''
    if 973 <= len(desc) <= 1024:
        report["warnings"].append(
            f"Description is {len(desc)} characters, within 5% of the 1024 limit. "
            f"The next trigger-phrase edit will breach it; trim now."
        )

    # Name portability advisory: at least one major client's own authoring
    # validator accepts only ASCII names, even though the spec and this
    # validator accept Unicode.
    name_val = frontmatter.get('name')
    name = name_val.strip() if isinstance(name_val, str) else ''
    if name and not name.isascii():
        report["warnings"].append(
            f"Name '{name}' contains non-ASCII characters. The spec and this validator "
            f"accept Unicode names, but at least one major client's own authoring tool "
            f"requires ASCII-only names and will reject this one. Prefer ASCII for "
            f"cross-client portability."
        )

    report["valid"] = len(report["errors"]) == 0
    return report


def validate_skill(skill_path):
    """Strict validation of a skill. Returns (is_valid, message).

    Wraps inspect_skill(..., mode="strict") for existing callers.
    Returns the first error message on failure, or (True, "Skill is valid!").
    """
    report = inspect_skill(skill_path, mode="strict")
    if report["valid"]:
        return True, "Skill is valid!"
    return False, report["errors"][0]


def body_warnings(skill_path):
    """Non-fatal advisories on the SKILL.md body budget. Returns a list of strings."""
    skill_path = Path(skill_path).resolve()
    skill_md = skill_path / 'SKILL.md'
    warnings = []
    if not skill_md.exists():
        return warnings
    content = skill_md.read_text()
    try:
        frontmatter, body = parse_frontmatter(content)
    except ValueError:
        return warnings
    lines = body.count('\n') + 1
    approx_tokens = len(body) // 4
    body_bytes = len(body.encode('utf-8'))
    if lines > BODY_LINE_BUDGET:
        warnings.append(
            f"SKILL.md body is {lines} lines (recommended under {BODY_LINE_BUDGET}). "
            f"Move detail into references/ and point to it."
        )
    if approx_tokens > BODY_TOKEN_BUDGET:
        warnings.append(
            f"SKILL.md body is roughly {approx_tokens} tokens (recommended under "
            f"{BODY_TOKEN_BUDGET}). Move detail into references/ and point to it."
        )
    if body_bytes > BODY_BYTE_BUDGET_CODEX:
        warnings.append(
            f"SKILL.md body is {body_bytes} bytes. Codex hard-truncates a selected "
            f"skill's body at about {BODY_BYTE_BUDGET_CODEX} bytes (~2000 tokens) by "
            f"default, well under the open standard's own 5000-token recommendation. "
            f"If you need Codex compatibility, trim well under this."
        )
    # Description ceiling advisory: within 5% of the 1024 limit is a maintenance trap.
    desc_val = frontmatter.get('description')
    desc = desc_val.strip() if isinstance(desc_val, str) else ''
    if 973 <= len(desc) <= 1024:
        warnings.append(
            f"Description is {len(desc)} characters, within 5% of the 1024 limit. "
            f"The next trigger-phrase edit will breach it; trim now."
        )
    # Name portability advisory: at least one major client's own authoring
    # validator accepts only ASCII names, even though the spec and this
    # validator accept Unicode.
    name_val = frontmatter.get('name')
    name = name_val.strip() if isinstance(name_val, str) else ''
    if name and not name.isascii():
        warnings.append(
            f"Name '{name}' contains non-ASCII characters. The spec and this validator "
            f"accept Unicode names, but at least one major client's own authoring tool "
            f"requires ASCII-only names and will reject this one. Prefer ASCII for "
            f"cross-client portability."
        )
    return warnings


def _format_report(report, skill_arg, json_output):
    """Print report and return exit code."""
    if json_output:
        print(json.dumps(report))
        return 0 if report["valid"] else 1

    for e in report["errors"]:
        print(f"  error: {e}")
    for w in report["warnings"]:
        print(f"  warning: {w}")
    if report["valid"]:
        print("Skill is valid!")
        if report["mode"] == "strict":
            print(f"  note: for the reference check, also run: skills-ref validate {skill_arg}")
            print("  note: skills-ref is the standard's reference/demonstration library, not a production SDK")
    return 0 if report["valid"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m scripts.quick_validate",
        description="Validate a skill directory (agentskills.io compliance).",
    )
    parser.add_argument("skill_directory", help="Path to the skill folder")
    parser.add_argument(
        "--mode",
        choices=["strict", "import"],
        default="strict",
        help="Validation mode: strict (portable) or import (compatibility inspection)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report")
    args = parser.parse_args(argv)

    report = inspect_skill(args.skill_directory, mode=args.mode)
    sys.exit(_format_report(report, args.skill_directory, args.json))


if __name__ == "__main__":
    main()