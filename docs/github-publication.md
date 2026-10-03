# GitHub publication

## Selected mechanism

Use a GitHub Check run for the verdict and a PR review submitted as `COMMENT` for the overview and inline discussions. Do not submit native `APPROVE` or `REQUEST_CHANGES` review events in the POC. GitHub Checks communicate the AI result; Deltahub owns export gate enforcement.

The Check is created with the reviewed `head_sha`. Creating a PR review or a new standalone inline review comment uses the explicit reviewed `commit_id`; never omit it and default to a newer commit. A reply inherits its existing review thread's location: GitHub ignores new anchor fields for `in_reply_to`. General PR comments have no commit-selection parameter, so their body and integration metadata identify the reviewed head/base. See the [review-comment API](https://docs.github.com/en/rest/pulls/comments#create-a-review-comment-for-a-pull-request). Keep PR identity, reviewed base, review ID, and report revision in integration metadata/summary. GitHub Checks are commit-specific, not a native head/base-pair or PR-specific gate. Different PRs or base snapshots sharing a head must retain distinct integration identities and Check IDs.

## Outcome mapping

| Worker result | Check status/conclusion | Meaning |
| --- | --- | --- |
| Running, including bounded quota waiting | `in_progress`, no conclusion | Review execution is active |
| Completed approved review | `completed` / `success` | This reviewed input has no active PR-related major/blocking findings |
| Completed review requiring changes | `completed` / `failure` | This reviewed input has active PR-related major/blocking findings |
| Required execution failure | `completed` / `action_required` | No new review verdict; retry or intervention required |
| Intentional stop before computation completed | `completed` / `cancelled` | Operational stop; no new code verdict |
| Execution deadline reached | `completed` / `timed_out` | No new review verdict if computation did not finish |

If computation already finished and publication failed, record delivery failure separately and reconcile it. Do not replace the computed code verdict with a claim about code quality merely because a network call failed. Do not mark a Check successful before required findings/overview delivery has been reconciled; preserve the computed verdict in GCS while delivery is pending.

**A newer head or base does not cancel this Check, suppress findings, or erase the historical verdict.** The worker publishes what it actually reviewed. Deltahub schedules the later review.

## Overview and inline findings

Render the review programmatically from validated structured outputs. No additional writer agent is needed. Include:

- Verdict, reviewed head and base, review ID, and report revision.
- A note if newer head/base information was observed at publication; no claim that this check is atomic with publication.
- Concise scope and quality-control summary.
- Active PR-related findings, severity, and valid/unverifiable status.
- Missing evidence needed to settle unverifiable findings.
- Prior findings fixed, invalidated, or explicitly dismissed, with source links where useful.
- A separate unrelated-findings section; explicitly say these do not block this PR.
- Material setup/context limitations and a link to the authenticated full report location or Deltahub job page. The report revision is reserved before publication and saved afterward, so the page may temporarily show publication in progress.
- Stable finding IDs and the configured explicit dismissal syntax, such as `@hubbot /dismiss finding-<UUIDv4>` with an optional explanation.

Use the explicit `primary_location` as the sole proposed anchor for a finding; other `locations` are supporting evidence, not extra comments. A null primary location uses the overview. Before an API request, validate the path, side, line/range, and any suggestion against the immutable reviewed diff, including deletions/renames. RIGHT coordinates refer to the reviewed head tree; LEFT coordinates refer to the comparison's merge-base tree. The GitHub request `commit_id` remains the reviewed head even for a LEFT anchor. A base-tip evidence location outside that diff is overview-only. Preserve historical evidence coordinates; never relabel old ledger lines with a new commit.

Post new actionable findings inline when a valid diff location exists. Use path, side, line/range, and the reviewed commit; preserve original coordinates. Missing requirements or conflicting Jira instructions may belong only in the overview. Include suggestion blocks only for verified replacements.

For existing findings, link to the known discussion instead of creating duplicates. AI-originated pushback receives a reply produced by discussion/reassessment. Human-authored threads are not automatically rebutted or resolved; the overview can explain the AI's assessment. Thread resolution is not proof that the issue was fixed or dismissed.

## Authoritative discussion links

Canonical findings and history entries carry `thread_links`: worker-owned typed links identifying the GitHub discussion kind, root object ID, optional review-thread ID, and display URL. Authenticated context remains the source of comment relationships. Publication objects record delivery outcomes; they do not establish a second independently editable thread registry. When an inline comment/reply is acknowledged, update the finding association in the publication checkpoint and final report before considering delivery reconciled. On recovery, reconstruct missing links from reconciled GitHub objects/markers. Preserve every legitimate association rather than replacing an older human or AI thread with a new duplicate.

The worker's accepted action record stores `proposed_replies` as reply_target_id and body per entry, copied from the verifier's final replies or a deterministic command acknowledgment. Code chooses the destination from the action's known source comments and the finding's stored associations, preferring the actual argument being answered; it validates that they belong to the same PR/finding. A general PR comment has no native inline-review reply destination: publish an explicitly linked PR comment instead. If the destination is missing or ambiguous, fetch authenticated context or fail the delivery operation; never send a reply to an agent-invented URL. `publication.objects[].reply_to` records the code-selected destination for an actual reply. Human-originated threads retain the no-automatic-rebuttal policy.

## Multiple reply targets and observed requirement changes

Route each reply_target_id independently using the worker's authenticated conversation mapping. Several targets can refer to the same finding; they can publish different bodies to different threads while sharing one lifecycle assessment. Persist each target's destination and acknowledged GitHub object separately. A retain_closure reply does not reopen the finding. Agent proposed_replies entries carry only target ID and body; final verifier replies additionally echo the fixed finding/source mapping for validation.

If authoritative Jira/rule changes were observed, state that the current verdict uses the supplied requirement snapshot and that Deltahub was notified a new request is needed. Preserve the reviewed head/base and actual verdict. This is informational drift reporting, not permission to approve a changed requirement input.

Reply publication keys include the logical review, immutable discussion/review request and reply target identity. Exact-input retry jobs reuse those keys; a response to a new triggering conversation must not overwrite an older dismissal acknowledgment merely because both concern the same finding.

## PR changes during execution

Suppose X is reviewed while Y is pushed:

1. Finish X using its fixed head/base and context.
2. Checkpoint X's computation and publication plan, including the reserved report revision.
3. Publish the overview and findings with X's commit identity.
4. Complete X's Check with X's actual verdict.
5. Save X's report with publication results, or with actual delivery failure details.
6. Return X's result to Deltahub. It must not satisfy Y's gate.

Reading the current PR before publication is optional informational context, not authorization to substitute code or suppress publication. Comments on older commits may appear outdated. GitHub can still reject an inline anchor; supplying an old commit does not guarantee every location remains accepted.

If GitHub rejects a specific anchor after validating our coordinates, render that finding in the overview with original file/line/commit information and, where available, a permalink to the reviewed code. Record the fallback. Do not relocate it onto newer code without review. Distinguish an anchor-validation failure from rate limiting, permission loss, or service failure; those are delivery errors requiring appropriate retry/reporting. A generic HTTP 422 alone is not sufficient to assume an anchor problem.

If a force-push makes the historical link unusable, retain the source evidence in the private report and still describe its original identity. Never fabricate a current-code link. PR closure, merge, or access changes can prevent some publication operations; preserve the result and report the actual delivery failure rather than inventing a new verdict.

## Publication records and retries

Use deterministic internal publication keys for the Check, overview, and each finding/reply. Checkpoint intended operations before sending requests and persist GitHub object IDs as acknowledged. The report itself is saved after publication; recovery cannot depend on a pre-publication report or a final shutdown callback. Before retrying after an ambiguous timeout, query/reconcile existing objects using the recorded identity and unobtrusive integration markers. Do not treat Check `external_id` as a uniqueness guarantee supplied by GitHub.

A create-review request submits the overview and its inline comments together. Treat that request as one publication operation: a validation rejection does not establish that any inline comment was created. Prevalidate every anchor. If GitHub rejects an identified anchor, move that finding to the overview, rebuild the request, and retry after reconciling any ambiguous outcome. Do not infer which comments succeeded within a rejected review request. If the API response does not identify the offending anchor reliably, reconcile first and fall back to an overview-only request rather than silently dropping findings. Generic validation failures unrelated to anchors remain delivery errors.

Partial delivery can occur across separate operations: for example, the review succeeds but a later reply or Check update fails. Persist acknowledged IDs and retry only missing operations after reconciliation. Individual-comment endpoints are also separate operations if used. All writes must be repeatable without duplicate comments; transient delivery errors do not justify rerunning agents.

Use one overview associated with a review identity, updating it for discussion and delivery-update revisions while retaining immutable report history. A successful retry after a saved delivery-failure report creates the next report revision with updated publication IDs/status; the assessment remains unchanged. No separate final delivery record is introduced. A new code-review identity gets its own overview. Concurrent discussion results must use revision checks so an older response cannot overwrite a newer result. Same-review publication requires serialization or equivalent coordination supplied by the integration.

## Permissions

The trusted publisher needs repository content read, pull requests read/write, and Checks read/write permissions through the GitHub App installation. If implementation uses issue comments instead of a review body for a fallback, account for the necessary permission explicitly. Agents' read tools must not inherit the publisher's write authority. Trusted worker code reads the App key from Secret Manager, generates scoped installation tokens and replaces them before expiry as needed. Clone/fetch/read adapters use separate read-only credentials. Never place keys or tokens in prompts, repository environments, reports or persisted Git URLs. If a worker is lost, Deltahub may close only an abandoned in-progress Check with an operational explanation; it leaves completed Checks intact, and the retry worker reconciles publication.

## References

- [Check runs API](https://docs.github.com/en/rest/checks/runs)
- [PR reviews API](https://docs.github.com/en/rest/pulls/reviews)
- [PR review comments API](https://docs.github.com/en/rest/pulls/comments)
- [Commit statuses API](https://docs.github.com/en/rest/commits/statuses)
- [Protected-branch review behavior](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
