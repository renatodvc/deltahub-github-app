# Deltahub AI review worker

An internal GitHub App worker, executed as a GCP Cloud Run Job, that reviews pull requests against Jira requirements and project rules using Codex subscription authentication.

**The POC specification is agreed. The worker is not implemented yet.** This repository contains the implementation contracts, prompt assets, synthetic fixtures, and local contract checks.

## Start here

1. Read the [specification](docs/specification.md) for scope, ownership, use cases, and the execution flow.
2. Follow the [team guide](CONTRIBUTING.md) to set up the contract checks and begin implementation.
3. Use the [documentation map](docs/README.md) to find the detailed workflow, contracts, runtime, and publication rules.
4. Work against the [acceptance scenarios and implementation sequence](docs/acceptance.md).

The worker owns review execution, investigation, reporting, and publication. Deltahub owns eligibility, ticket/PR resolution, scheduling, and customer-export gates. A result applies only to the exact review input it identifies.

## Repository map

| Location | Purpose |
| --- | --- |
| [docs](docs/README.md) | Agreed behavior, integration requirements, decisions, and acceptance criteria |
| [schemas](schemas/README.md) | v0.1 request, stage, report, event, and recovery contracts |
| [prompts](prompts/README.md) | Versioned app-owned policy and role prompts |
| [examples](examples/README.md) | Synthetic contract fixtures for learning and regression checks |
| [scripts](scripts/README.md) | Contract-suite compatibility command and agent-schema bundling |
| [tests](docs/testing.md) | One pytest suite for contracts, units, offline integrations and opt-in live checks |

## Run the tests

With `uv` and the Python version required by [pyproject.toml](pyproject.toml):

```sh
uv sync --locked --group specs
uv run --locked --group specs python -m pytest
```

These checks do not call Codex, GitHub, Jira, Deltahub, or GCP. Deployment and live integration verification remain implementation work. See [decisions and feasibility checks](docs/decisions.md); subscription-authentication applicability remains outside this specification’s scope.
