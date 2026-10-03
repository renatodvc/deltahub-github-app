# Writing and maintaining tests

Keep one pytest suite, one configuration in `pyproject.toml`, and one normal offline command:

```sh
uv sync --locked --group specs
uv run --locked --group specs python -m pytest
```

Use a path or `-k` to focus on a change. Run the full offline suite before handoff. CI runs this same suite plus Ruff. A passing suite currently proves the contracts and local tooling; the worker has not been implemented.

## Where a test belongs

| Location | What belongs here |
| --- | --- |
| `tests/contracts/` | Schema/example compatibility, prompt provenance, reference contract invariants |
| `tests/unit/` | One implemented rule or component, with dependencies controlled |
| `tests/integration/` | Real components working together, with external services replaced at their boundaries |
| `tests/live/` | Explicitly selected checks against real development services |
| `tests/support/` | Small shared builders, reusable fakes, and reference assertions |

Organize files by capability, such as publication or recovery, not by ticket number, review round, or the agent that wrote them. Extend the nearest existing module before creating another. Do not introduce another test root, runner, framework, or parallel fixture collection. Directory names assign pytest markers automatically.

The canonical JSON examples stay in [examples](../examples/README.md). `tests/support/contract_checks.py` loads a fresh copy with `read(name)` and holds the migrated reference assertions. Those assertions are not production validation. As worker behavior is implemented, test its actual entry points; do not copy its decision logic into test helpers and call that implementation coverage.

## Writing a useful case

1. Identify the observable behavior and the existing test that comes closest. State what would break if this behavior regressed.
2. Use the lowest level that proves it. A unit test usually fits a verdict rule; an integration test fits persistence followed by publication. Keep live tests small and focused on assumptions a fake cannot establish.
3. Make setup, action, and expected result readable. Name the test after behavior, for example `test_retry_does_not_publish_a_second_comment`.
4. Assert meaningful results: returned state, stored artifacts, emitted events, or externally visible effects. Assert calls only when the interaction is itself the requirement. Avoid private-method ordering and whole-object snapshots for unrelated fields.
5. Cover the relevant success, failure, and boundary cases. Parameterize variations of the same rule with descriptive IDs; use separate tests for different behavior.
6. For a bug fix, reproduce the failure before fixing it when practical. A new test must fail for the relevant wrong behavior, not merely exercise the code.

Do not target a test count or blanket coverage percentage. Prioritize our consequential rules: exact-commit verdicts, required-stage completion, idempotent publication, immutable retry inputs, evidence-based lifecycle changes, stop/recovery, and credential handling. Keep one primary home for each rule; repeat it at a higher level only when that checks a distinct integration risk.

## Fixtures and dependencies

- Start with explicit local setup. Use a local fixture when several tests in that module need the same resource. Move it to `tests/support/` only when multiple modules need it.
- Shared builders return fresh objects and expose only useful variations. Avoid giant default payloads, mutable globals, nested fixture chains, and helpers with many boolean switches.
- Keep `tests/conftest.py` limited to suite policy and genuinely common fixtures. Avoid hidden autouse setup, apart from documented isolation rules.
- Reuse canonical examples for contract tests. For focused worker tests, build the smallest valid input that expresses the behavior; do not copy entire JSON examples into another directory.
- Use `tmp_path` for files and repositories, `monkeypatch` for environment changes, and function-scoped mutable resources. Clean up resources even on assertion failure. Tests must run individually and in any order.
- Replace GitHub, Jira, GCS, Deltahub and Codex at the application boundary. Reuse a small fake per interface when needed; do not implement a second service simulator or build speculative fakes before the interface exists. Exercise real serialization/transport code in adapter tests.
- Use injected clocks and scripted outcomes for timeouts, rate limits and retries. Do not wait 30 minutes, sleep to synchronize, or depend on current time. Use explicit bounded synchronization for concurrency tests.

## Offline, live, and model evaluation

The normal suite needs no credentials, external services, model calls, or network. Python sockets are blocked by `pytest-socket`. Live modules are excluded from normal discovery, and network access is enabled only for tests under `tests/live/` when explicitly requested:

```sh
uv run --locked --group specs python -m pytest tests/live --run-live
```

`-m live` alone does not opt in. Do not enable sockets in offline tests or globally. Keep imports and collection free of side effects. The socket guard is not an OS sandbox: it cannot prevent a child process such as `curl` or `git` from reaching the network. Offline subprocess tests must run known local operations, use bounded timeouts, and require no credentials. See [pytest-socket](https://github.com/miketheman/pytest-socket) for the guard's scope.

There are no real-service tests yet. When adding one, document its development account/resources, minimum permissions, required environment variables, and cleanup next to the tests. Never commit secrets or load a developer's personal credentials implicitly. Give created resources unique identifiers; delete only resources the test created. An explicitly selected live test must fail clearly when its setup is missing, rather than silently skip.

For deterministic workflow tests, script Codex responses, including malformed output, rate limits and crashes. Actual model review quality needs a separate, explicitly invoked evaluation using curated cases and a rubric. Do not assert exact generated prose or make stochastic model results a normal unit-test gate. Keep any evaluation runner in this same testing structure when it is introduced.

## Before handing off a change

- Reuse existing helpers and remove obsolete cases when replacing behavior. Keep examples, contracts and tests consistent.
- Run the focused tests, then the full offline command, `uv run --locked ruff check tests scripts`, `uv run --locked ruff format --check tests scripts`, and `git diff --check`. Extend lint paths when application source is added.
- Report what behavior was tested and any integration that remains unverified. Do not claim fixture checks prove live authentication or model quality.
- Do not hide failures with retries, arbitrary sleeps, broad exception handling, weakened assertions, or unexplained skips. A temporary quarantine needs a tracked issue, an owner and a removal condition.

For AI-assisted work: read this guide and neighboring tests first. Identify where the new case fits, reuse the existing setup, and review the resulting diff for duplicated fixtures and tests that merely mirror the implementation.
