"""Shared utilities for skill-maker scripts."""

import re

import yaml

_FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---\n?(.*)$', re.DOTALL)


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
