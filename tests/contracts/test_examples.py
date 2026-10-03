"""Validate the canonical examples without making a second fixture collection."""

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.bundle_agent_schema import AGENT_OUTPUTS, bundle
from tests.support import contract_checks as checks


@pytest.mark.parametrize("schema_name", sorted(checks.SCHEMAS))
def test_schema_is_valid(schema_name):
    Draft202012Validator.check_schema(checks.SCHEMAS[schema_name])


@pytest.mark.parametrize("role", AGENT_OUTPUTS)
def test_agent_bundle_uses_supported_structure(role):
    schema = bundle(role)
    checks.subset(schema)
    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize("entry", checks.read("manifest"), ids=lambda entry: entry["file"])
def test_canonical_example(entry):
    name = entry["file"].removesuffix(".json")
    schema = Path(entry["schema"]).name.removesuffix(".schema.json")
    value = checks.read(name)
    checks.validate(schema, value)
    if "context" in value:
        checks.context_sources(value["context"])
    if schema == "job-event":
        checks.event(value)
        if value["report"] is not None:
            serialized = (json.dumps(value["report"], indent=2) + "\n").encode()
            assert value["report_artifact"]["sha256"] == hashlib.sha256(serialized).hexdigest()
    if schema == "report-coordination":
        checks.coordination(value)
    if schema == "import-accounting":
        checks.import_accounting(value)
    role = schema.removesuffix("-output")
    if role in AGENT_OUTPUTS and schema.endswith("-output"):
        Draft202012Validator(bundle(role)).validate(value)
        checks.agent(role, value)
    if schema == "review-report":
        checks.report(value)
        if value["request_id"] == "request-retained-discussion":
            request = "retained-closure-discussion-request"
        elif value["mode"] == "discussion":
            request = "discussion-request"
        elif value["review_id"] == "review-2":
            request = "follow-up-request"
        else:
            request = "review-request"
        assert value["input"]["input_sha256"] == value["input"]["payload"]["sha256"]
        assert value["input"]["input_sha256"] == checks.digest(request)
    if schema.endswith("-input"):
        checks.prompt(value["prompt"])
        checks.stage_prompt(value)
    if schema == "verifier-input":
        checks.historical(value)


def test_manifest_covers_every_example_once():
    names = [entry["file"] for entry in checks.read("manifest")]
    assert len(names) == len(set(names))
    assert set(names) == {p.name for p in (checks.ROOT / "examples").glob("*.json")} - {
        "manifest.json"
    }
