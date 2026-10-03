"""Exercise the actual CLI with disposable files and no external services."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("write_file", [False, True], ids=["stdout", "output-file"])
def test_cli_emits_schema_accepted_by_validator(tmp_path, write_file):
    output = tmp_path / "reviewer.schema.json"
    command = [sys.executable, str(ROOT / "scripts/bundle_agent_schema.py"), "reviewer"]
    if write_file:
        command.extend(["--output", str(output)])
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=10)

    assert result.returncode == 0, result.stderr
    schema = json.loads(output.read_text() if write_file else result.stdout)
    Draft202012Validator.check_schema(schema)
    fixture = json.loads((ROOT / "examples/reviewer-output.json").read_text())
    Draft202012Validator(schema).validate(fixture)
    if write_file:
        assert result.stdout == ""


def test_cli_rejects_unknown_role(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/bundle_agent_schema.py"), "unknown"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert "invalid choice" in result.stderr
