"""Check local documentation references and source whitespace without network access."""

import re

import pytest

from tests.support.contract_checks import ROOT

DOCUMENTS = sorted(
    {
        *ROOT.glob("*.md"),
        *(
            path
            for folder in ("docs", "schemas", "examples", "prompts", "scripts", "tests")
            for path in (ROOT / folder).rglob("*.md")
        ),
    }
)
SOURCES = sorted(
    path
    for folder in ("docs", "schemas", "examples", "prompts", "scripts", "tests")
    for path in (ROOT / folder).rglob("*")
    if path.is_file() and path.suffix in (".md", ".json", ".py")
)


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda path: str(path.relative_to(ROOT)))
def test_local_markdown_links_resolve(path):
    for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
        if "://" not in link and not link.startswith("#"):
            assert (path.parent / link.split("#")[0]).exists(), f"{path}: broken link {link}"


@pytest.mark.parametrize("path", SOURCES, ids=lambda path: str(path.relative_to(ROOT)))
def test_source_has_no_trailing_whitespace(path):
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        assert line == line.rstrip(), f"{path}:{number}: trailing whitespace"
