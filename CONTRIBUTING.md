# Team guide

The agreed POC behavior is defined in [the specification](docs/specification.md) and its supporting references. Implement that behavior; do not treat synthetic fixture values or reference-validator shortcuts as additional product requirements. If implementation exposes a conflict or a material feasibility issue, record it explicitly before changing the contract.

## Local setup

The repository uses `uv`; its development Python requirement is declared in [pyproject.toml](pyproject.toml). This development environment is separate from the repository-specific runtime profiles used by the future worker.

Install the development and contract dependencies, then run the offline suite:

```sh
uv sync --locked --group specs
uv run --locked --group specs python -m pytest
```

Keep dependency changes and `uv.lock` together. The `specs` group supplies `jsonschema` and `referencing`; it does not install an agent runtime or application dependencies.

## Reading and implementation order

Start with the [overview and flow](docs/specification.md), then read the [workflow](docs/agent-workflow.md) and [contracts](docs/contracts.md). Runtime/authentication, tools, and GitHub publication are mapped in [docs/README.md](docs/README.md).

The [implementation sequence](docs/acceptance.md#implementation-sequence) provides a suggested delivery order. All acceptance scenarios remain part of the POC. The [feasibility checks](docs/decisions.md#required-feasibility-checks) distinguish platform evidence still needed from settled product decisions.

## How the supporting files will be used

- **Schemas:** validate worker inputs/outputs and integration boundaries. Agent output schemas are mechanically bundled before they are supplied to the runtime.
- **Prompts:** app-owned runtime assets. Mandatory policy, role customization, and recorded provenance must follow the specified assembly rules.
- **Examples:** executable documentation and seed fixtures for implementation tests. They are not deployment configurations, live credentials, or captured agent runs.
- **Contract tests:** the canonical pytest regression suite; `scripts/validate_specs.py` is only a compatibility wrapper. Helpers in `tests/support/contract_checks.py` illustrate selected semantic rules; they are not the production orchestrator or a complete runtime validator. Build production validators against the documented rules and test them using the fixtures.
- **Bundling script:** a small reusable utility for preparing agent schemas. Integration must still verify the bundled schemas against the pinned runtime.

## Maintaining the baseline

Keep schema, prose, prompts, fixtures, and validation expectations consistent when an explicitly agreed change is made. Do not weaken a check merely to make an example pass.

Examples are indexed by [examples/manifest.json](examples/manifest.json). Preserve existing fixture paths when possible: the validator references some by name. Add a fixture and manifest entry for a new scenario, and add an input-dependent check when schema validation cannot establish the intended rule.

Some fixtures embed exact prompt text, serialized reports, and artifact SHA-256 values. When their source changes, update the dependent snapshots and hashes in dependency order. Do not replace real fixture hashes with placeholders or bypass digest checks. Synthetic remote artifact references are identified as such in the [example guide](examples/README.md).

Follow [the testing guide](docs/testing.md) for test placement, shared fixtures, offline isolation, and live checks. Run the full offline suite, Ruff and `git diff --check` before handoff. Live integration tests must additionally demonstrate authentication, SDK behavior, sandbox boundaries, publication, and recovery; passing local fixtures is not evidence that those integrations work.
