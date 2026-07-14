#!/usr/bin/env python3
"""
Quick validation script for skills - zero-network spec checker.

Fallback for the canonical validator `skills-ref validate ./your-skill`. Enforces the
agentskills.io frontmatter constraints and emits soft warnings on the SKILL.md body
budget. Keeps the validate_skill(skill_path) -> (bool, message) contract that
package_skill.py imports.
"""

import sys
import re
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


def _counts_as_skill_md(rel_path):
    """True if a SKILL.md at rel_path (relative to the skill root) would be packaged."""
    dir_parts = rel_path.parts[:-1]
    if any(part in EXCLUDED_DIR_PARTS for part in dir_parts):
        return False
    if dir_parts and dir_parts[0] in ROOT_EXCLUDED_DIR_PARTS:
        return False
    return True


def validate_skill(skill_path):
    """Basic validation of a skill. Returns (is_valid, message)."""
    skill_path = Path(skill_path).resolve()

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # A skill must contain exactly one SKILL.md, at <folder>/SKILL.md. Extra
    # (nested) SKILL.md files are rejected on upload: hosts that accept a .skill
    # upload accept exactly one per skill - only a filesystem-based client loads
    # nested ones. package_skill produces an upload-bound .skill, so block here
    # rather than ship an artifact that's guaranteed to fail on upload.
    skill_md_files = [
        p for p in skill_path.rglob('SKILL.md')
        if _counts_as_skill_md(p.relative_to(skill_path))
    ]
    if len(skill_md_files) > 1:
        extras = sorted(
            str(p.relative_to(skill_path)) for p in skill_md_files
            if p.resolve() != skill_md.resolve()
        )
        return False, (
            f"Found {len(skill_md_files)} SKILL.md files, but a skill must contain "
            f"exactly one at <folder>/SKILL.md. Hosts that accept a .skill upload reject "
            f"multiple on upload (only a filesystem-based client loads nested skills). "
            f"Extra: {', '.join(extras)}.\n"
            "  - Separate skills: package each on its own, or build a plugin "
            "(skills/<name>/SKILL.md).\n"
            "  - Supporting docs: rename to non-SKILL.md files (e.g. references/<topic>.md).\n"
            "  - Swept in by mistake: package only the one skill directory."
        )

    # Read and validate frontmatter
    content = skill_md.read_text()
    try:
        frontmatter, _body = parse_frontmatter(content)
    except ValueError as e:
        return False, str(e)

    # Define allowed properties (the six recognized agentskills.io fields)
    ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}. "
            f"Nonstandard fields are not portable; put environment needs in 'compatibility'."
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        # Check naming convention (kebab-case: lowercase with hyphens)
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        # Check name length (max 64 characters per spec)
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."
        # Name must match the parent directory name (spec requirement)
        dir_name = skill_path.name
        if dir_name and name != dir_name:
            return False, (
                f"Name '{name}' must match the parent directory name '{dir_name}'. "
                f"Rename the directory or the 'name' field so they are identical."
            )

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if not description:
        return False, "Description must be non-empty."
    # Check for angle brackets
    if '<' in description or '>' in description:
        return False, "Description cannot contain angle brackets (< or >)"
    # Check description length (max 1024 characters per spec)
    if len(description) > 1024:
        return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."

    # Validate compatibility field if present (optional, max 500 chars)
    compatibility = frontmatter.get('compatibility', '')
    if compatibility:
        if not isinstance(compatibility, str):
            return False, f"Compatibility must be a string, got {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"Compatibility is too long ({len(compatibility)} characters). Maximum is 500 characters."

    # Validate metadata is a string->string map if present (optional)
    metadata = frontmatter.get('metadata')
    if metadata is not None:
        if not isinstance(metadata, dict):
            return False, f"Metadata must be a mapping, got {type(metadata).__name__}"

    return True, "Skill is valid!"


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
    # Description ceiling advisory: within 5% of the 1024 limit is a maintenance trap.
    desc = (frontmatter.get('description') or '').strip()
    if 973 <= len(desc) <= 1024:
        warnings.append(
            f"Description is {len(desc)} characters, within 5% of the 1024 limit. "
            f"The next trigger-phrase edit will breach it; trim now."
        )
    return warnings


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.quick_validate <skill_directory>")
        sys.exit(1)

    target = sys.argv[1]
    valid, message = validate_skill(target)
    print(message)
    if valid:
        for w in body_warnings(target):
            print(f"  warning: {w}")
        print("  note: for the canonical check, also run: skills-ref validate " + target)
    sys.exit(0 if valid else 1)
