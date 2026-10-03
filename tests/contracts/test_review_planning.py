"""Contract rejection cases; each mutation gets a fresh canonical example."""

import copy

import pytest
from jsonschema import ValidationError

from tests.support import contract_checks as checks


def custom_rule_input():
    value = checks.read("reviewer-input")
    value["custom_rules"] = [{"rule_id": "test-plan", "text": "Require a test plan."}]
    value["assignment"]["expected_custom_rule_ids"] = ["test-plan"]
    return value


@pytest.mark.parametrize(
    "example_name, mutate, check",
    [
        pytest.param(
            "reviewer-output",
            lambda d: d.update(reviewer_id="fake"),
            lambda d: checks.validate("reviewer-output", d),
            id="worker_owned_reviewer_id",
        ),
        pytest.param(
            "reviewer-output",
            lambda d: d["findings"][0]["locations"][0].update(commit_sha="f" * 40),
            lambda d: checks.validate("reviewer-output", d),
            id="worker_owned_commit_sha",
        ),
        pytest.param(
            "reviewer-quality-output",
            lambda d: d["quality_control"]["built_in"].pop("english"),
            lambda d: checks.validate("reviewer-output", d),
            id="missing_english_check",
        ),
        pytest.param(
            "reviewer-output",
            lambda d: d["findings"][0].pop("rule_id"),
            lambda d: checks.validate("reviewer-output", d),
            id="missing_rule_id",
        ),
        pytest.param(
            "reviewer-output",
            lambda d: d["findings"][0].update(
                category="custom_rule", severity="minor", rule_id="x"
            ),
            lambda d: checks.agent("reviewer", d),
            id="custom_rule_severity",
        ),
        pytest.param(
            "reviewer-output",
            lambda d: d["findings"][0].update(evidence=[]),
            lambda d: checks.agent("reviewer", d),
            id="empty_evidence",
        ),
        pytest.param(
            "reviewer-output",
            lambda d: d["findings"][0]["locations"][0].update(start_line=0),
            lambda d: checks.agent("reviewer", d),
            id="zero_line_number",
        ),
        pytest.param(
            "reviewer-quality-output",
            lambda d: d.update(quality_control=None),
            lambda d: checks.agent("reviewer", d, checks.read("reviewer-input")),
            id="missing_quality_control",
        ),
        pytest.param(
            "reviewer-quality-output",
            lambda d: None,
            lambda d: checks.agent("reviewer", d, custom_rule_input()),
            id="missing_custom_rule_result",
        ),
        pytest.param(
            "reviewer-custom-rules-output",
            lambda d: d["quality_control"]["custom_rules"].extend(
                copy.deepcopy(d["quality_control"]["custom_rules"])
            ),
            lambda d: checks.agent("reviewer", d, custom_rule_input()),
            id="duplicate_custom_rule_result",
        ),
        pytest.param(
            "triage-output",
            lambda d: d["assignments"][0].update(mandatory_lens_ids=[]),
            lambda d: checks.agent("triage", d, checks.read("triage-input")),
            id="missing_mandatory_lens",
        ),
        pytest.param(
            "aggregate-singleton-output",
            lambda d: d["groups"][0].update(
                merged_text=checks.read("aggregate-output")["groups"][0]["merged_text"]
            ),
            lambda d: checks.agent("aggregate", d),
            id="singleton_rewrite",
        ),
        pytest.param(
            "aggregate-output",
            lambda d: d["groups"][0]["input_ids"].pop(),
            lambda d: checks.agent("aggregate", d, checks.read("aggregate-input")),
            id="omitted_aggregate_candidate",
        ),
        pytest.param(
            "aggregate-output",
            lambda d: d["groups"][0]["input_ids"].append("fake"),
            lambda d: checks.agent("aggregate", d, checks.read("aggregate-input")),
            id="foreign_aggregate_candidate",
        ),
    ],
)
def test_rejects_invalid_contract(example_name, mutate, check):
    value = checks.read(example_name)
    mutate(value)
    with pytest.raises((ValueError, ValidationError)):
        check(value)


def test_quality_owner_accepts_complete_custom_rule_result():
    checks.agent("reviewer", checks.read("reviewer-custom-rules-output"), custom_rule_input())
