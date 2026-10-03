"""Bundle local schema references only; never transform or discard validation rules."""

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_OUTPUTS = ("history-import", "triage", "reviewer", "aggregate", "verifier", "discussion")


def bundle(role):
    if role not in AGENT_OUTPUTS:
        raise ValueError(f"Unknown agent role: {role}")
    path = ROOT / "schemas" / f"{role}-output.schema.json"
    definitions = {}

    def visit(node, origin):
        if isinstance(node, list):
            return [visit(value, origin) for value in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            file, _, fragment = node["$ref"].partition("#")
            target = (origin.parent / file).resolve() if file else origin
            if target.parent != ROOT / "schemas":
                raise ValueError("Only references inside the schema bundle are allowed")
            value = json.loads(target.read_text())
            for part in fragment.lstrip("/").split("/") if fragment else []:
                value = value[part.replace("~1", "/").replace("~0", "~")]
            key = (
                target.stem.replace(".schema", "")
                + "__"
                + fragment.replace("/", "_").replace("$", "")
            )
            if key not in definitions:
                definitions[key] = {}  # Permit internal recursive definitions.
                definitions[key] = visit(value, target)
            return {"$ref": "#/$defs/" + key}
        return {
            key: visit(value, origin)
            for key, value in node.items()
            if key not in ("$id", "$schema")
        }

    result = visit(copy.deepcopy(json.loads(path.read_text())), path)
    result["$defs"] = definitions
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=AGENT_OUTPUTS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(bundle(args.role), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")
