"""Shared utilities for skill-maker scripts."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

import yaml

_FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---\n?(.*)$', re.DOTALL)

# Paths excluded from a built or installed skill. Kept here rather than in
# package_skill.py so the packager and the installer share one rule set.
EXCLUDE_DIRS = {"__pycache__", "node_modules", ".pytest_cache"}
EXCLUDE_GLOBS = {"*.pyc"}
EXCLUDE_FILES = {".DS_Store"}
# Directories excluded only at the skill root (not when nested deeper).
ROOT_EXCLUDE_DIRS = {"evals", "tests"}


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Split SKILL.md content into (frontmatter dict, body).

    Raises ValueError if the frontmatter delimiters are missing, or the
    frontmatter is not valid YAML, or is not a mapping.
    """
    if not content.startswith('---'):
        raise ValueError("No YAML frontmatter found")

    match = _FRONTMATTER_RE.match(content)
    if not match:
        raise ValueError("Invalid frontmatter format")

    frontmatter_text, body = match.group(1), match.group(2)
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}") from e

    if not isinstance(frontmatter, dict):
        raise ValueError("Frontmatter must be a YAML dictionary")

    return frontmatter, body


def should_exclude(rel_path: Path) -> bool:
    """Check if a path should be excluded from a built or installed skill.

    `rel_path` is relative to the skill's parent directory, so its first
    component is the skill folder name.
    """
    parts = rel_path.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    # parts[0] is the skill folder name and parts[1] (if present) is the first
    # subdir, so root-only exclusions do not apply to nested directories.
    if len(parts) > 1 and parts[1] in ROOT_EXCLUDE_DIRS:
        return True
    name = rel_path.name
    if name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_GLOBS)


def walk_skill(skill_path):
    """Yield (file_path, arcname, excluded) for every file under a skill.

    `arcname` is relative to the skill's parent directory, so it carries the
    skill folder name as its first component. Callers decide whether to skip
    excluded entries; this is the single source of the build rules.

    The path is resolved first so the invariant holds even when the caller
    passes `.` or another relative path: without it, `Path('.').parent` is
    `.` and the folder-name prefix is lost.
    """
    skill_path = Path(skill_path).resolve()
    for file_path in sorted(skill_path.rglob("*")):
        if not file_path.is_file():
            continue
        arcname = file_path.relative_to(skill_path.parent)
        yield file_path, arcname, should_exclude(arcname)
