import unittest

from scripts.utils import parse_frontmatter


class TestParseFrontmatter(unittest.TestCase):
    def test_parses_frontmatter_and_body(self):
        content = "---\nname: my-skill\ndescription: Does a thing.\n---\nBody text.\n"
        frontmatter, body = parse_frontmatter(content)
        self.assertEqual(frontmatter, {"name": "my-skill", "description": "Does a thing."})
        self.assertEqual(body, "Body text.\n")

    def test_missing_opening_delimiter_raises(self):
        with self.assertRaisesRegex(ValueError, "No YAML frontmatter found"):
            parse_frontmatter("name: my-skill\ndescription: Does a thing.\n")

    def test_missing_closing_delimiter_raises(self):
        with self.assertRaisesRegex(ValueError, "Invalid frontmatter format"):
            parse_frontmatter("---\nname: my-skill\ndescription: Does a thing.\n")

    def test_invalid_yaml_raises(self):
        with self.assertRaisesRegex(ValueError, "Invalid YAML in frontmatter"):
            parse_frontmatter("---\nname: [unclosed\n---\nBody.\n")

    def test_non_mapping_frontmatter_raises(self):
        with self.assertRaisesRegex(ValueError, "Frontmatter must be a YAML dictionary"):
            parse_frontmatter("---\n- just\n- a\n- list\n---\nBody.\n")

    def test_empty_body_is_empty_string(self):
        frontmatter, body = parse_frontmatter("---\nname: my-skill\n---\n")
        self.assertEqual(frontmatter, {"name": "my-skill"})
        self.assertEqual(body, "")


if __name__ == "__main__":
    unittest.main()
