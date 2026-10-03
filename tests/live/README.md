# Live development checks

No live tests are implemented yet. This directory is reserved for real GitHub, Jira, GCP, Deltahub and Codex integration checks; ordinary tests use local substitutes.

Run explicitly with `uv run --locked --group specs python -m pytest tests/live --run-live` once tests exist. Without tests, pytest exits with its normal “no tests collected” status. The normal suite excludes this directory.

For each integration added, document the required development resources, environment variable names, permissions and cleanup here. Keep secrets out of the repository. Selected tests must fail clearly if configuration is missing. Read [the testing guide](../../docs/testing.md) before adding cases.
