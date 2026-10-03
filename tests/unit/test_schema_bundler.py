"""Focused tests of the real schema-bundling utility."""

import json

import pytest

from scripts import bundle_agent_schema as bundler


def test_unknown_role_is_rejected():
    with pytest.raises(ValueError, match="Unknown agent role"):
        bundler.bundle("invented-role")


def test_bundling_preserves_constraints_and_source_files(tmp_path, monkeypatch):
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    role = schemas / "reviewer-output.schema.json"
    common = schemas / "common.schema.json"
    role.write_text(
        json.dumps(
            {
                "type": "object",
                "properties": {"name": {"$ref": "common.schema.json#/$defs/name"}},
                "required": ["name"],
                "additionalProperties": False,
            }
        )
    )
    common.write_text(json.dumps({"$defs": {"name": {"type": "string", "enum": ["allowed"]}}}))
    before = {path: path.read_bytes() for path in (role, common)}
    monkeypatch.setattr(bundler, "ROOT", tmp_path)

    result = bundler.bundle("reviewer")

    assert result["required"] == ["name"]
    assert result["additionalProperties"] is False
    reference = result["properties"]["name"]["$ref"]
    assert reference.startswith("#/$defs/")
    assert result["$defs"][reference.removeprefix("#/$defs/")] == {
        "type": "string",
        "enum": ["allowed"],
    }
    assert {path: path.read_bytes() for path in before} == before


def test_reference_cannot_escape_schema_directory(tmp_path, monkeypatch):
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "reviewer-output.schema.json").write_text(json.dumps({"$ref": "../outside.json"}))
    monkeypatch.setattr(bundler, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Only references inside the schema bundle"):
        bundler.bundle("reviewer")
