# Contract tooling

These scripts support implementation and maintenance of the specification. They do not run reviews or contact external services.

## Validate specifications

From the repository root:

```sh
uv run --locked --group specs python -m pytest tests/contracts
```

The canonical suite in `tests/contracts/` checks:

- Every declared schema and fixture in the example manifest.
- The six bundled agent-output schemas and their structural subset.
- Representative input-dependent rules, rejection cases, and report invariants.
- Recorded prompt/report digests and selected artifact relationships.
- Local Markdown file links and trailing whitespace.

`validate_specs.py` delegates to this same pytest suite and propagates its exit status; it has no separate checks or runner logic. CI runs the whole offline suite. Semantic helpers in `tests/support/contract_checks.py` are test/reference code, not a production validation API; the full implementation requirements are in [schema-validation.md](../docs/schema-validation.md).

## Bundle an agent output schema

```sh
uv run --locked --group specs python scripts/bundle_agent_schema.py reviewer --output /tmp/reviewer-output.schema.json
```

Supported roles are `history-import`, `triage`, `reviewer`, `aggregate`, `verifier`, and `discussion`. Omitting `--output` prints JSON to stdout.

The bundler uses the Python standard library. It resolves repository-local references into one schema; it does not translate constraints or create an independently maintained contract. Generated bundles are disposable build outputs, not additional source schemas. The implementation can reuse this utility while verifying compatibility with its pinned runtime.

## Fixtures and dependencies

The [development and specs dependency groups](../pyproject.toml) declare the test dependencies, locked in [uv.lock](../uv.lock). See the [team guide](../CONTRIBUTING.md) for setup. The [example catalog](../examples/README.md) explains scenario boundaries and synthetic artifact references.
