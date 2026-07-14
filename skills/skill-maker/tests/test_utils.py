import pytest

from scripts.utils import parse_frontmatter


def test_parses_frontmatter_and_body():
    content = "---\nname: my-skill\ndescription: Does a thing.\n---\nBody text.\n"
    frontmatter, body = parse_frontmatter(content)
    assert frontmatter == {"name": "my-skill", "description": "Does a thing."}
    assert body == "Body text.\n"


def test_missing_opening_delimiter_raises():
    with pytest.raises(ValueError, match="No YAML frontmatter found"):
        parse_frontmatter("name: my-skill\ndescription: Does a thing.\n")


def test_missing_closing_delimiter_raises():
    with pytest.raises(ValueError, match="Invalid frontmatter format"):
        parse_frontmatter("---\nname: my-skill\ndescription: Does a thing.\n")


def test_invalid_yaml_raises():
    with pytest.raises(ValueError, match="Invalid YAML in frontmatter"):
        parse_frontmatter("---\nname: [unclosed\n---\nBody.\n")


def test_non_mapping_frontmatter_raises():
    with pytest.raises(ValueError, match="Frontmatter must be a YAML dictionary"):
        parse_frontmatter("---\n- just\n- a\n- list\n---\nBody.\n")


def test_empty_body_is_empty_string():
    frontmatter, body = parse_frontmatter("---\nname: my-skill\n---\n")
    assert frontmatter == {"name": "my-skill"}
    assert body == ""
