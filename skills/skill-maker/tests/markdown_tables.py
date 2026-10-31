"""Markdown table parsing shared by the tests that check tables in the skill's docs."""

import re


def table_rows(text):
    """Yield each body row of every pipe table in `text` as a dict keyed by its header cells."""
    header = None
    for line in text.splitlines():
        if not line.startswith("|"):
            header = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
        elif not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            yield dict(zip(header, cells))


def table_header(text):
    """Return the header cells of the first pipe table in `text`, or an empty list."""
    for line in text.splitlines():
        if line.startswith("|"):
            return [cell.strip() for cell in line.strip().strip("|").split("|")]
    return []
