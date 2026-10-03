# Shared test support

`contract_checks.py` contains the original validator's reference assertions and fresh JSON loader. These are contract checks, not the future worker's production validators. The canonical fixtures remain in [examples](../../examples/README.md).

Add a small builder or fake here only when multiple test modules need it. Return fresh mutable state; keep domain setup out of the root `conftest.py`. Do not create speculative service clients before the application has an interface to replace. Follow the [testing guide](../../docs/testing.md).
