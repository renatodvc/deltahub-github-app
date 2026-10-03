"""Exercise the collection policy in isolated miniature pytest projects."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def policy_project(pytester):
    tests = pytester.path / "tests"
    tests.mkdir()
    (tests / "conftest.py").write_text((ROOT / "tests/conftest.py").read_text())
    pytester.makeini("""
        [pytest]
        testpaths = tests
        addopts = --disable-socket --strict-markers --strict-config
        markers =
            unit: unit
            live: live
    """)
    for folder in ("unit", "live"):
        (tests / folder).mkdir()
    return pytester


def test_offline_socket_use_fails(policy_project):
    (policy_project.path / "tests/unit/test_network.py").write_text(
        "import socket\ndef test_network():\n    socket.socket()\n"
    )
    result = policy_project.runpytest_subprocess("-q", timeout=30)
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*SocketBlockedError*"])


def test_live_module_is_not_imported_by_default(policy_project):
    (policy_project.path / "tests/unit/test_local.py").write_text("def test_local(): pass\n")
    (policy_project.path / "tests/live/test_remote.py").write_text(
        'raise RuntimeError("live module was imported")\n'
    )
    result = policy_project.runpytest_subprocess("-q", timeout=30)
    result.assert_outcomes(passed=1)


def test_live_opt_in_only_enables_live_sockets(policy_project):
    # Opening an unconnected socket verifies the guard; neither test contacts a service.
    (policy_project.path / "tests/live/test_remote.py").write_text(
        "import socket\ndef test_remote():\n    with socket.socket(): pass\n"
    )
    (policy_project.path / "tests/unit/test_local.py").write_text(
        "import socket\nimport pytest\nfrom pytest_socket import SocketBlockedError\n"
        "def test_local():\n    with pytest.raises(SocketBlockedError): socket.socket()\n"
    )
    result = policy_project.runpytest_subprocess("--run-live", "-q", timeout=30)
    result.assert_outcomes(passed=2)


def test_offline_tests_cannot_opt_themselves_into_network(policy_project):
    (policy_project.path / "tests/unit/test_network.py").write_text(
        "import pytest\n@pytest.mark.enable_socket\ndef test_network(): pass\n"
    )
    result = policy_project.runpytest_subprocess("-q", timeout=30)
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*network-enabled tests belong in tests/live*"])
