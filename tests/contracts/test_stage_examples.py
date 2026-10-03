"""Examples must agree with the inputs from which each agent works."""

import pytest

from tests.support import contract_checks as checks


@pytest.mark.parametrize(
    "role, output_name, input_name",
    [
        ("history-import", "history-import-output", "history-import-input"),
        ("triage", "triage-output", "triage-input"),
        ("reviewer", "reviewer-quality-output", "reviewer-input"),
        ("aggregate", "aggregate-output", "aggregate-input"),
        (
            "aggregate",
            "single-reviewer-history-aggregate-output",
            "single-reviewer-history-aggregate-input",
        ),
        ("verifier", "discussion-verifier-output", "discussion-verifier-input"),
        ("verifier", "two-history-verifier-output", "two-history-verifier-input"),
        ("verifier", "multi-thread-verifier-output", "multi-thread-verifier-input"),
        ("verifier", "retained-closure-verifier-output", "retained-closure-verifier-input"),
        ("discussion", "discussion-output", "discussion-input"),
        ("discussion", "discussion-reassessment-output", "discussion-reassessment-input"),
        ("reviewer", "closed-history-reviewer-output", "closed-history-reviewer-input"),
        ("verifier", "closed-history-verifier-output", "closed-history-verifier-input"),
        ("history-import", "history-import-correction-output", "history-import-correction-input"),
        (
            "history-import",
            "history-import-no-assertion-output",
            "history-import-no-assertion-input",
        ),
        ("reviewer", "import-omission-reviewer-output", "import-omission-reviewer-input"),
        ("reviewer", "import-corrected-reviewer-output", "import-corrected-reviewer-input"),
        ("verifier", "follow-up-verifier-output", "follow-up-verifier-input"),
        ("verifier", "review-multi-thread-verifier-output", "review-multi-thread-verifier-input"),
    ],
    ids=lambda value: value,
)
def test_agent_output_matches_input(role, output_name, input_name):
    checks.agent(role, checks.read(output_name), checks.read(input_name))
