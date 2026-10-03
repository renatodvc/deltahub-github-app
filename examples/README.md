# Contract examples

These synthetic JSON fixtures are executable documentation and a starting point for implementation tests. Keep them as regression coverage. They are not deployment payloads or recorded model runs.

[manifest.json](manifest.json) is the complete machine-readable catalog: each entry maps a fixture to its schema. The [validator](../scripts/README.md) checks every entry. Start with the main review below, then use the scenario groups for specific behavior.

Repository names, model IDs, SHA values, secret references, object generations and URLs are fictional. Timeout values and the two-minute finalization reserve are illustrative settings, not agreed defaults. Prompt texts are snapshots of the real [app-owned assets](../prompts/README.md), with reproducible digests. References to remote artifacts do not claim that those GCS objects exist.

Scenarios are alternatives, not a single continuous history. They may reuse synthetic IDs; production finding IDs remain globally unique and are never recycled. Some stage inputs intentionally exercise follow-up/history behavior independently of the main output example. Use the manifest and scenario descriptions rather than assuming similarly named files form one complete run.

The main review has two reviewers discover the same input-handling bug. Aggregation produces one candidate; independent verification confirms it. GitHub publication succeeds, and report revision 1 records the published objects.

## Core review and stage outputs

- [Invocation](job-invocation.json) and [immutable review request](review-request.json) separate per-job metadata from reusable input. [Retry invocation](retry-invocation.json) has a new linked job but points to the same request/object generation.
- [Triage](triage-output.json), [technical reviewer](reviewer-output.json), [quality reviewer](reviewer-quality-output.json), [aggregation](aggregate-output.json), [verification](verifier-output.json), [report](review-report.json), and [finished event](job-event.json) form the main example.
- [Empty reviewer](reviewer-empty-output.json) is successful. [Singleton aggregation](aggregate-singleton-output.json) preserves its input; Python rejects replacement text. [Custom-rule results](reviewer-custom-rules-output.json) assume a `test-plan` rule in an independent scenario.
- [Unverifiable assessment](verifier-unverifiable-output.json) and [report](review-report-unverifiable.json) demonstrate a blocking uncertainty. [Failed report](review-report-failed.json) preserves one reviewer while another exhausts its attempts; no verification ran.

## History, discussion, and replies

- [Follow-up request](follow-up-request.json), [verifier input](follow-up-verifier-input.json), [output](follow-up-verifier-output.json), and [report](follow-up-report.json) preserve/assess unresolved history despite zero discoveries. The verifier replies and code derives actions; current-c2 maps to the stable finding despite historical c1. No reconciliation agent runs.
- [Discussion request](discussion-request.json) uses `@hubbot /dismiss finding-11111111-1111-4111-8111-111111111111` from a non-author human and references the already-published report revision 1. [Input](discussion-input.json) carries the validated command. [Empty agent output](discussion-output.json) illustrates that no technical proposals are needed; an actual command-only invocation skips agents. [Discussion report revision 2](discussion-report.json) records the deterministic override and acknowledgment, preserving the original verification.
- [Technical discussion input](discussion-reassessment-input.json) and [provisional output](discussion-reassessment-output.json) propose accepting an author's objection. The [independent verifier input](discussion-verifier-input.json) and [output](discussion-verifier-output.json) instead confirm the defect and supply the final reply. Code derives the confirm action; there is no third discussion reconciliation stage. This is an alternative to the dismissal scenario, not a later event in it.
- [One-reviewer rediscovery input](single-reviewer-history-aggregate-input.json) and [output](single-reviewer-history-aggregate-output.json) merge a new raw issue with seeded history despite only one discovering reviewer.
- [Review-mode multiple-conversation input](review-multi-thread-verifier-input.json) and [output](review-multi-thread-verifier-output.json) show the same final-reply contract as discussion mode.
- [Omitted finding IDs](discussion-derived-target-request.json) and [empty finding IDs](discussion-empty-target-request.json) are accepted requests; the worker resolves the explicit dismissal target from the triggering comment.
- [Closed-history reviewer input](closed-history-reviewer-input.json) and [output](closed-history-reviewer-output.json) retain one fixed issue despite an unrelated same-file edit and select a dismissed issue because a new caller changes its assumptions. [Verifier input](closed-history-verifier-input.json) and [output](closed-history-verifier-output.json) independently confirm both the issue and the relevant change before code may reactivate it.
- [Multiple conversation input](multi-thread-verifier-input.json) and [output](multi-thread-verifier-output.json) return two replies for one finding, keyed by separate target IDs.
- [Retained closure input](retained-closure-verifier-input.json), [output](retained-closure-verifier-output.json), and [accepted action in the report](retained-closure-report.json) preserve a dismissal while answering a new comment.
- [Two historical bindings](two-history-verifier-input.json) and [assessments](two-history-verifier-output.json) exercise source-derived identity checks. [Retained-closure discussion request](retained-closure-discussion-request.json) and [completed report](retained-closure-report.json) demonstrate the two-agent path through final serialization after an earlier human dismissal.

## Human import and coverage correction

- [Human import input](history-import-input.json) and [output](history-import-output.json) distinguish an asserted defect from praise. [Verifier input](human-import-verifier-input.json) shows worker-stamped human origin and a null prior assessment before independent verification.
- [Missed accounting](import-accounting-missed.json) includes a defect incorrectly classified as empty plus genuine praise. [Reviewer input](import-omission-reviewer-input.json) and [provisional output](import-omission-reviewer-output.json) identify the omission without a new AI finding.
- [Correction input](history-import-correction-input.json) and [output](history-import-correction-output.json) extract the assertion. [Updated accounting](import-accounting-corrected.json) preserves the human ID and correction artifacts; [updated reviewer input](import-corrected-reviewer-input.json) retains the original thread and [accepted output](import-corrected-reviewer-output.json) acknowledges revision 2 before independent verification.
- [Non-assertion correction input](history-import-no-assertion-input.json) and [output](history-import-no-assertion-output.json) explain why praise contains no defect; the owner must subsequently accept that disposition.
- [Empty accounting](import-accounting-empty.json) is explicit even when no human import work exists. Missing accounting, stale acknowledgments, foreign source IDs, missing resolutions, lost provenance/thread links and exhausted/reset correction budgets are rejected by representative checks.

## Failure, retries, and publication

- [Computation-complete event](job-event-review-completed.json) references a checkpoint with no final report. [Failure-only event](job-event-failed.json) references retained work without requiring report composition.
- [Delivery-failed report](delivery-failed-report.json) is the publication-first failure fallback; [delivery-retried revision](delivery-retried-report.json) shows the same assessment with a new linked job and successful publication. These are alternatives to the main successful revision 1.
- [Stopped report](stopped-report.json) and [event](job-event-stopped.json) show a known stop before computation completes, preserving progress with no verdict.
- [Computation retry report](computation-retried-report.json) follows the failed revision-1 scenario with revision 2, execution_retry, and a new linked job. [Its event](job-event-retry-finished.json) expects revision 1. [Reserved coordination](report-coordination-reserved.json) and [saved coordination](report-coordination-saved.json) show the corresponding GCS states; object generations are API metadata, not duplicated inside the records.
- [Delivery-failed event](job-event-delivery-failed.json) carries the typed failure from its completed-computation report. [Early Check event](job-event-check-registered.json) provides Deltahub the Check ID/owner before any final report exists.
- [Report-storage failure event](job-event-report-storage-failed.json) references completed computation without pretending that a final report was uploaded.
- [Requirement-change event](job-event-context-changed.json) and [report](context-changed-report.json) record a live change while retaining the original review input.
- [Recovery claim](report-coordination-recovering.json), [finalized recovery checkpoint](reservation-recovery-finalized.json), and [released coordination](report-coordination-recovered.json) preserve the last completed assessment while finalizing a stopped predecessor.
- Retry reports identify reused stages and their original completion artifacts; all reports carry a worker-owned required-stage plan.

## Prompt customization and source metadata

- [Custom prompt request](custom-prompts-request.json) and [resolved reviewer input](custom-prompts-reviewer-input.json) demonstrate role replacement plus additions while retaining mandatory policy.
- [Metadata-only request](metadata-only-request.json) resolves typed source IDs and their URI/observation times without documents or duplicate descriptions.
- [Custom import request](custom-prompts-history-import-request.json) and [resolved input](custom-prompts-history-import-input.json) demonstrate separate discussion/import replacements and independent import model/timeout settings. Only the import replacement appears in the import prompt; mandatory policy remains.

The remaining general stage inputs are [triage](triage-input.json), [reviewer](reviewer-input.json), and [aggregate](aggregate-input.json). Preserve fixture paths unless the manifest, validator references, and documentation are updated together. See the [team guide](../CONTRIBUTING.md#maintaining-the-baseline) for snapshot and hash maintenance.
