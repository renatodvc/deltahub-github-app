"""Cross-example identities, immutable artifacts, and delivery-only updates."""

import copy

import pytest

from tests.support import contract_checks as checks


@pytest.mark.parametrize("name", ["follow-up-request", "discussion-request"])
def test_request_references_existing_baseline(name):
    request = checks.read(name)
    artifact = (
        request["baseline_report"]
        if name == "follow-up-request"
        else request["discussion"]["previous_report"]
    )
    assert artifact["sha256"] == checks.digest("review-report")
    assert request["created_at"] >= checks.read("review-report")["created_at"]


@pytest.mark.parametrize(
    "event_name, report_name",
    [("job-event", "review-report"), ("job-event-stopped", "stopped-report")],
)
def test_event_embeds_matching_report(event_name, report_name):
    event = checks.read(event_name)
    assert event["report"] == checks.read(report_name)
    assert event["report_artifact"]["sha256"] == checks.digest(report_name)


def test_failed_event_retains_checkpoint_digest():
    artifact = checks.read("job-event-failed")["failure"]["retained_artifacts"][0]
    assert artifact["sha256"] == checks.digest("reviewer-output")


def test_retry_changes_job_but_preserves_request_and_payload():
    original, retry = checks.read("job-invocation"), checks.read("retry-invocation")
    assert original["job_id"] != retry["job_id"]
    assert original["request_id"] == retry["request_id"]
    assert original["payload_uri"] == retry["payload_uri"]
    assert original["payload_generation"] == retry["payload_generation"]
    assert retry["job_lineage"]["retry_of_job_id"] == original["job_id"]


def test_delivery_retry_advances_revision():
    before, after = checks.read("delivery-failed-report"), checks.read("delivery-retried-report")
    assert after["report_revision"] == before["report_revision"] + 1
    assert after["revision_reason"] == "delivery_update"


@pytest.mark.parametrize(
    "field", ["findings", "raw_findings", "quality_checks", "verdict", "target", "input"]
)
def test_delivery_retry_preserves_computation(field):
    before = checks.read("delivery-failed-report")[field]
    after = checks.read("delivery-retried-report")[field]
    if field == "findings":
        for finding in before + after:
            finding.pop("thread_links")  # Successful publication adds delivery associations.
    assert before == after


def test_single_candidate_skips_deduplication():
    report = checks.read("follow-up-report")
    assert report["stats"]["dedup_input_count"] == 1
    assert all(
        stage["status"] == "skipped"
        for stage in report["stages"]
        if stage["kind"] == "deduplication"
    )


def test_stop_after_computation_retains_verdict_without_claiming_delivery():
    report = checks.read("review-report")
    verdict = copy.deepcopy(report["verdict"])
    report.update(execution_status="stopped", stop=checks.read("stopped-report")["stop"])
    report["stop"].update(requested_at="2026-10-01T12:04:31Z", observed_at="2026-10-01T12:04:32Z")
    report["publication"].update(status="not_started", objects=[])
    checks.validate("review-report", report)
    checks.report(report)
    assert report["verdict"] == verdict
