"""Contract rejection cases; each mutation gets a fresh canonical example."""

import pytest
from jsonschema import ValidationError

from tests.support import contract_checks as checks


@pytest.mark.parametrize(
    "example_name, mutate, check",
    [
        pytest.param(
            "discussion-report",
            lambda d: d["dismissals"][0]["actor"].update(is_pr_author=True),
            checks.report,
            id="author_cannot_dismiss",
        ),
        pytest.param(
            "job-event-review-completed",
            lambda d: d.update(checkpoint=None),
            lambda d: checks.validate("job-event", d),
            id="completion_without_checkpoint",
        ),
        pytest.param(
            "job-event-review-completed",
            lambda d: d.update(report=checks.read("review-report")),
            lambda d: checks.validate("job-event", d),
            id="premature_completion_report",
        ),
        pytest.param(
            "job-event",
            lambda d: d["report"]["publication"].update(status="pending"),
            lambda d: checks.validate("job-event", d),
            id="finished_event_pending_publication",
        ),
        pytest.param(
            "stopped-report",
            lambda d: d.update(verdict="approved"),
            lambda d: checks.validate("review-report", d),
            id="stopped_review_approval",
        ),
        pytest.param(
            "job-event-stopped",
            lambda d: d.update(stop=None),
            lambda d: checks.validate("job-event", d),
            id="stopped_event_without_intent",
        ),
        pytest.param(
            "job-event-failed",
            lambda d: d["failure"].update(code="unknown"),
            lambda d: checks.validate("job-event", d),
            id="unknown_failure_code",
        ),
        pytest.param(
            "review-report",
            lambda d: d["findings"][0].update(thread_links=[]),
            checks.report,
            id="published_finding_without_thread",
        ),
        pytest.param(
            "review-report",
            lambda d: d["findings"][0].update(finding_id="finding-1"),
            lambda d: checks.validate("review-report", d),
            id="non_global_finding_id",
        ),
        pytest.param(
            "delivery-failed-report",
            lambda d: d.update(delivery_failure=None),
            lambda d: checks.validate("review-report", d),
            id="missing_delivery_failure",
        ),
        pytest.param(
            "delivery-failed-report",
            lambda d: d["delivery_failure"].update(code="stage_attempts_exhausted"),
            lambda d: checks.validate("review-report", d),
            id="computation_error_as_delivery_error",
        ),
        pytest.param(
            "computation-retried-report",
            lambda d: d["reservation"].update(expected_report_revision=None),
            checks.report,
            id="missing_revision_predecessor",
        ),
        pytest.param(
            "report-coordination-reserved",
            lambda d: d["active_reservation"].update(report_revision=1),
            checks.coordination,
            id="reservation_reuses_revision",
        ),
        pytest.param(
            "job-event-retry-finished",
            lambda d: d.update(expected_report_revision=None),
            checks.event,
            id="event_missing_revision_precondition",
        ),
        pytest.param(
            "job-event-delivery-failed",
            lambda d: d["failure"].update(code="github_access_denied"),
            checks.event,
            id="delivery_event_wrong_cause",
        ),
        pytest.param(
            "job-event-check-registered",
            lambda d: d.update(check=None),
            lambda d: checks.validate("job-event", d),
            id="registration_without_check",
        ),
        pytest.param(
            "job-event-check-registered",
            lambda d: d["check"].update(owner_job_id="old-job"),
            checks.event,
            id="check_owned_by_other_job",
        ),
        pytest.param(
            "job-event-report-storage-failed",
            lambda d: d.update(checkpoint=None),
            lambda d: checks.validate("job-event", d),
            id="storage_failure_without_checkpoint",
        ),
        pytest.param(
            "job-event-report-storage-failed",
            lambda d: d["failure"].update(code="github_delivery_failed"),
            lambda d: checks.validate("job-event", d),
            id="storage_failure_wrong_code",
        ),
        pytest.param(
            "job-event-context-changed",
            lambda d: d["context_change"].update(policy="use_latest"),
            lambda d: checks.validate("job-event", d),
            id="changed_context_adopts_latest",
        ),
        pytest.param(
            "context-changed-report",
            lambda d: d["context_changes"][0].update(new_request_required=False),
            lambda d: checks.validate("review-report", d),
            id="changed_context_without_new_request",
        ),
        pytest.param(
            "report-coordination-recovering",
            lambda d: d["recovery"].update(predecessor_terminal_state="running"),
            lambda d: checks.validate("report-coordination", d),
            id="recovery_of_running_execution",
        ),
        pytest.param(
            "report-coordination-recovering",
            lambda d: d.update(active_reservation=None),
            checks.coordination,
            id="recovery_without_reservation",
        ),
        pytest.param(
            "report-coordination-recovering",
            lambda d: d["recovery"].update(predecessor_execution_id="unrelated-job"),
            checks.coordination,
            id="wrong_recovery_predecessor",
        ),
        pytest.param(
            "report-coordination-recovered",
            lambda d: d.update(last_completed_revision=3),
            checks.coordination,
            id="completed_revision_ahead_of_saved",
        ),
        pytest.param(
            "reservation-recovery-finalized",
            lambda d: d.update(terminal_report=None),
            lambda d: checks.validate("reservation-recovery", d),
            id="finalized_recovery_without_report",
        ),
        pytest.param(
            "reservation-recovery-finalized",
            lambda d: d.update(publication_checkpoint=None),
            lambda d: checks.validate("reservation-recovery", d),
            id="finalized_recovery_without_publication_checkpoint",
        ),
        pytest.param(
            "review-report",
            lambda d: d["stages"][2].update(status="failed"),
            checks.report,
            id="failed_required_stage",
        ),
        pytest.param(
            "review-report",
            lambda d: d["stages"].pop(2),
            checks.report,
            id="missing_required_stage",
        ),
        pytest.param(
            "review-report",
            lambda d: d["required_stage_ids"].remove("r1"),
            checks.report,
            id="omitted_required_stage_id",
        ),
        pytest.param(
            "review-report",
            lambda d: d["stages"][2].update(completion_artifact=None),
            checks.report,
            id="success_without_completion_artifact",
        ),
        pytest.param(
            "review-report",
            lambda d: d["stages"][5].update(status="pending"),
            checks.report,
            id="pending_composition",
        ),
        pytest.param(
            "review-report",
            lambda d: d.update(computation_plan=None),
            checks.report,
            id="missing_computation_plan",
        ),
        pytest.param(
            "delivery-retried-report",
            lambda d: d["stages"][1]["reused_from"]["completion_artifact"].update(sha256="0" * 64),
            checks.report,
            id="reused_artifact_digest_mismatch",
        ),
        pytest.param(
            "retained-closure-report",
            lambda d: d["stages"].pop(0),
            checks.report,
            id="missing_retained_closure_stage",
        ),
        pytest.param(
            "review-report",
            lambda d: d["stages"][1].update(kind="finding_reconciliation"),
            lambda d: checks.validate("review-report", d),
            id="removed_reconciliation_stage",
        ),
        pytest.param(
            "job-event-failed",
            lambda d: d["failure"].update(code="reverification_limit_exceeded"),
            lambda d: checks.validate("job-event", d),
            id="removed_reverification_failure_code",
        ),
        pytest.param(
            "review-report",
            lambda d: d.update(import_accounting=None),
            lambda d: checks.validate("review-report", d),
            id="report_without_import_accounting",
        ),
        pytest.param(
            "review-report",
            lambda d: d["quality_checks"][0]["results"].update(
                import_omissions=checks.read("import-omission-reviewer-output")["quality_control"][
                    "import_omissions"
                ]
            ),
            checks.report,
            id="report_with_pending_omission",
        ),
    ],
)
def test_rejects_invalid_contract(example_name, mutate, check):
    value = checks.read(example_name)
    mutate(value)
    with pytest.raises((ValueError, ValidationError)):
        check(value)
