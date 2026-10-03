"""Shared collection policy only. Put capability-specific fixtures near their tests."""

from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

SUITES = {"contracts", "unit", "integration", "live"}


def pytest_addoption(parser):
    parser.addoption(
        "--run-live", action="store_true", help="Enable tests against development services"
    )


def pytest_configure(config):
    # Network access is granted per live test, never to the entire run.
    if (
        config.getoption("force_enable_socket")
        or config.getoption("allow_hosts")
        or config.getoption("allow_unix_socket")
    ):
        raise pytest.UsageError(
            "Use tests/live with --run-live; global socket overrides are disabled."
        )


def pytest_ignore_collect(collection_path, config):
    live = Path(__file__).parent / "live"
    if not config.getoption("--run-live") and collection_path.is_relative_to(live):
        return True
    return None


def pytest_collection_modifyitems(config, items):
    selected, deselected = [], []
    root = Path(__file__).parent
    for item in items:
        relative = item.path.relative_to(root)
        suite = relative.parts[0]
        if suite not in SUITES:
            raise pytest.UsageError(f"{item.nodeid}: put tests in one of {sorted(SUITES)}")
        if suite != "live" and (
            item.get_closest_marker("live")
            or item.get_closest_marker("enable_socket")
            or item.get_closest_marker("allow_hosts")
            or "socket_enabled" in item.fixturenames
        ):
            raise pytest.UsageError(f"{item.nodeid}: network-enabled tests belong in tests/live")
        item.add_marker(getattr(pytest.mark, suite))
        if suite == "live":
            if not config.getoption("--run-live"):
                deselected.append(item)
                continue
            item.add_marker(pytest.mark.enable_socket)
        selected.append(item)
    items[:] = selected
    if deselected:
        config.hook.pytest_deselected(items=deselected)
