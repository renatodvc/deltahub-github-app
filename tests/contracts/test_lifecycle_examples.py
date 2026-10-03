"""Reference lifecycle invariants; future worker tests must call the real orchestrator."""

import pytest

from tests.support import contract_checks as checks


@pytest.mark.parametrize("fixed, expected", [(False, "confirm"), (True, "mark_fixed")])
def test_independent_verifier_controls_discussion_action(fixed, expected):
    inp = checks.read("discussion-verifier-input")
    out = checks.read("discussion-verifier-output")
    finding_id = inp["assessment_bindings"][0]["finding_id"]
    assert inp["proposed_reassessments"][0]["assessment"]["status"] == "invalid"
    if fixed:
        out["assessments"][0].update(status="invalid", invalid_reason="fixed_in_reviewed_code")
    checks.agent("verifier", out, inp)
    assert checks.verified_actions(inp, out)[finding_id] == expected


@pytest.mark.parametrize("relevant_change", [True, False])
def test_closed_finding_needs_verified_change_to_reactivate(relevant_change):
    out = checks.read("closed-history-verifier-output")
    out["closure_assessments"][0]["relevant_change_confirmed"] = relevant_change
    assert (
        checks.may_reactivate(out["assessments"][0], out["closure_assessments"][0])
        is relevant_change
    )


@pytest.mark.parametrize("purpose", ["review", "discussion"])
def test_reply_preserves_retained_closure(purpose):
    inp, out = (
        checks.read("retained-closure-verifier-input"),
        checks.read("retained-closure-verifier-output"),
    )
    inp["purpose"] = purpose
    if purpose == "review":
        inp["proposed_reassessments"] = []
    checks.agent("verifier", out, inp)
    finding_id = inp["history_ledger"][0]["finding_id"]
    assert checks.verified_actions(inp, out)[finding_id] == "retain_closure"
    assert (
        checks.read("retained-closure-report")["finding_actions"][0]["action"] == "retain_closure"
    )


@pytest.mark.parametrize("purpose", ["review", "discussion"])
@pytest.mark.parametrize(
    "status, reason, expected",
    [
        ("valid", None, "confirm"),
        ("invalid", "refuted", "invalidate"),
        ("invalid", "fixed_in_reviewed_code", "mark_fixed"),
        ("unverifiable", None, "leave_unverifiable"),
    ],
)
def test_both_modes_derive_same_lifecycle_action(purpose, status, reason, expected):
    inp, out = checks.read("follow-up-verifier-input"), checks.read("follow-up-verifier-output")
    inp["purpose"] = purpose
    out["assessments"][0].update(
        status=status,
        invalid_reason=reason,
        missing_evidence=["Need runtime evidence"] if status == "unverifiable" else [],
        resolution_needed="Provide a focused reproduction" if status == "unverifiable" else None,
    )
    checks.agent("verifier", out, inp)
    finding_id = inp["assessment_bindings"][0]["finding_id"]
    assert checks.verified_actions(inp, out)[finding_id] == expected


def test_follow_up_report_uses_verified_actions_and_replies():
    checks.derived_actions_match(
        checks.read("follow-up-verifier-input"),
        checks.read("follow-up-verifier-output"),
        checks.read("follow-up-report")["finding_actions"],
    )


def test_multi_thread_example_covers_both_conversations():
    assert len(checks.read("multi-thread-verifier-output")["final_replies"]) == 2
