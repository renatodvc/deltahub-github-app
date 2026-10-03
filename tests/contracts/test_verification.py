"""Contract rejection cases; each mutation gets a fresh canonical example."""

import copy

import pytest
from jsonschema import ValidationError

from tests.support import contract_checks as checks


def swap_known_bindings(value):
    bindings = value["assessment_bindings"]
    bindings[0]["candidate_id"], bindings[1]["candidate_id"] = (
        bindings[1]["candidate_id"],
        bindings[0]["candidate_id"],
    )


@pytest.mark.parametrize(
    "example_name, mutate, check",
    [
        pytest.param(
            "verifier-output",
            lambda d: d["assessments"][0].update(status="invalid", invalid_reason=None),
            lambda d: checks.agent("verifier", d),
            id="invalid_without_reason",
        ),
        pytest.param(
            "verifier-output",
            lambda d: d["assessments"][0].update(invalid_reason="refuted"),
            lambda d: checks.agent("verifier", d),
            id="valid_with_invalid_reason",
        ),
        pytest.param(
            "verifier-unverifiable-output",
            lambda d: d["assessments"][0].update(missing_evidence=[]),
            lambda d: checks.agent("verifier", d),
            id="unverifiable_without_gap",
        ),
        pytest.param(
            "verifier-input",
            lambda d: d.update(candidates=[]),
            checks.historical,
            id="missing_history_candidate",
        ),
        pytest.param(
            "discussion-reassessment-output",
            lambda d: d.update(actions=[]),
            lambda d: checks.validate("discussion-output", d),
            id="empty_discussion_actions",
        ),
        pytest.param(
            "discussion-reassessment-output",
            lambda d: d.update(proposed_reassessments=[]),
            lambda d: checks.agent("discussion", d, checks.read("discussion-reassessment-input")),
            id="missing_reassessment",
        ),
        pytest.param(
            "discussion-verifier-output",
            lambda d: d.update(final_replies=[]),
            lambda d: checks.agent("verifier", d, checks.read("discussion-verifier-input")),
            id="missing_discussion_reply",
        ),
        pytest.param(
            "discussion-verifier-output",
            lambda d: d["final_replies"].append(copy.deepcopy(d["final_replies"][0])),
            lambda d: checks.agent("verifier", d, checks.read("discussion-verifier-input")),
            id="duplicate_discussion_reply",
        ),
        pytest.param(
            "discussion-verifier-output",
            lambda d: d["final_replies"][0].update(finding_id="unknown"),
            lambda d: checks.agent("verifier", d, checks.read("discussion-verifier-input")),
            id="unknown_reply_finding",
        ),
        pytest.param(
            "discussion-verifier-output",
            lambda d: d["final_replies"][0].update(source_comment_ids=["wrong"]),
            lambda d: checks.agent("verifier", d, checks.read("discussion-verifier-input")),
            id="wrong_reply_sources",
        ),
        pytest.param(
            "discussion-verifier-input",
            lambda d: d["assessment_bindings"][0].update(candidate_id="wrong"),
            lambda d: checks.agent("verifier", checks.read("discussion-verifier-output"), d),
            id="wrong_assessment_binding",
        ),
        pytest.param(
            "discussion-verifier-output",
            lambda d: d["assessments"][0].update(
                status="invalid",
                invalid_reason="fixed_in_reviewed_code",
                evidence=[dict(d["assessments"][0]["evidence"][0], location=None)],
            ),
            lambda d: checks.agent("verifier", d, checks.read("discussion-verifier-input")),
            id="fix_without_code_location",
        ),
        pytest.param(
            "closed-history-reviewer-output",
            lambda d: d["quality_control"]["closed_finding_decisions"].pop(),
            lambda d: checks.agent("reviewer", d, checks.read("closed-history-reviewer-input")),
            id="missing_closed_finding_decision",
        ),
        pytest.param(
            "closed-history-reviewer-output",
            lambda d: d["quality_control"]["closed_finding_decisions"][0].update(
                change_evidence=[]
            ),
            lambda d: checks.agent("reviewer", d, checks.read("closed-history-reviewer-input")),
            id="reassessment_without_change_evidence",
        ),
        pytest.param(
            "closed-history-reviewer-output",
            lambda d: d["quality_control"]["closed_finding_decisions"].append(
                copy.deepcopy(d["quality_control"]["closed_finding_decisions"][0])
            ),
            lambda d: checks.agent("reviewer", d, checks.read("closed-history-reviewer-input")),
            id="duplicate_closed_finding_decision",
        ),
        pytest.param(
            "closed-history-verifier-output",
            lambda d: d.update(closure_assessments=[]),
            lambda d: checks.agent("verifier", d, checks.read("closed-history-verifier-input")),
            id="missing_closure_assessment",
        ),
        pytest.param(
            "two-history-verifier-input",
            swap_known_bindings,
            lambda d: checks.agent("verifier", checks.read("two-history-verifier-output"), d),
            id="swapped_known_bindings",
        ),
        pytest.param(
            "two-history-verifier-input",
            lambda d: d["candidates"][1]["source_input_ids"].append(
                d["candidates"][0]["source_input_ids"][0]
            ),
            lambda d: checks.agent("verifier", checks.read("two-history-verifier-output"), d),
            id="duplicate_historical_membership",
        ),
        pytest.param(
            "retained-closure-report",
            lambda d: d.update(finding_actions=[]),
            checks.report,
            id="missing_retained_closure_action",
        ),
        pytest.param(
            "multi-thread-verifier-output",
            lambda d: d["final_replies"].pop(),
            lambda d: checks.agent("verifier", d, checks.read("multi-thread-verifier-input")),
            id="missing_conversation_reply",
        ),
        pytest.param(
            "multi-thread-verifier-output",
            lambda d: d["final_replies"][1].update(
                reply_target_id=d["final_replies"][0]["reply_target_id"]
            ),
            lambda d: checks.agent("verifier", d, checks.read("multi-thread-verifier-input")),
            id="duplicate_reply_target",
        ),
        pytest.param(
            "follow-up-verifier-output",
            lambda d: d.update(final_replies=[]),
            lambda d: checks.agent("verifier", d, checks.read("follow-up-verifier-input")),
            id="missing_review_reply",
        ),
        pytest.param(
            "follow-up-verifier-output",
            lambda d: d["final_replies"][0].update(finding_id="wrong"),
            lambda d: checks.agent("verifier", d, checks.read("follow-up-verifier-input")),
            id="wrong_review_reply_finding",
        ),
        pytest.param(
            "follow-up-verifier-output",
            lambda d: d["final_replies"][0].update(thread_url="https://wrong.invalid"),
            lambda d: checks.validate("verifier-output", d),
            id="agent_supplied_reply_url",
        ),
        pytest.param(
            "follow-up-report",
            lambda d: d["finding_actions"][0].update(action="invalidate"),
            lambda d: checks.derived_actions_match(
                checks.read("follow-up-verifier-input"),
                checks.read("follow-up-verifier-output"),
                d["finding_actions"],
            ),
            id="unverified_action_rewrite",
        ),
        pytest.param(
            "follow-up-report",
            lambda d: d["finding_actions"][0]["proposed_replies"][0].update(
                body="Unverified rewrite"
            ),
            lambda d: checks.derived_actions_match(
                checks.read("follow-up-verifier-input"),
                checks.read("follow-up-verifier-output"),
                d["finding_actions"],
            ),
            id="unverified_reply_rewrite",
        ),
    ],
)
def test_rejects_invalid_contract(example_name, mutate, check):
    value = checks.read(example_name)
    mutate(value)
    with pytest.raises((ValueError, ValidationError)):
        check(value)
