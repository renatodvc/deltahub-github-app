# Worker and Deltahub contracts

- [Invocation and immutable input](#invocation-and-immutable-input)
- [Identities](#identities)
- [Configuration](#configuration)
- [Context and lazy reads](#context-and-lazy-reads)
- [Frozen authoritative requirements and change notifications](#frozen-authoritative-requirements-and-change-notifications)
- [Agent inputs and outputs](#agent-inputs-and-outputs)
- [Human import coverage contracts](#human-import-coverage-contracts)
- [Discussion and closure contracts](#discussion-and-closure-contracts)
- [Reports and artifacts](#reports-and-artifacts)
- [Revision reservation and retry completion](#revision-reservation-and-retry-completion)
- [Abandoned reservation cleanup without resuming the request](#abandoned-reservation-cleanup-without-resuming-the-request)
- [Deltahub API operations](#deltahub-api-operations)
- [Progress event kinds](#progress-event-kinds)
- [Early Check registration and delivery diagnostics](#early-check-registration-and-delivery-diagnostics)
- [Failure and acknowledgment semantics](#failure-and-acknowledgment-semantics)
- [Storage failure after completed computation](#storage-failure-after-completed-computation)
- [Failure codes and retry guidance](#failure-codes-and-retry-guidance)
- [Schemas and examples](#schemas-and-examples)

The JSON schemas are the agreed v0.1 serialization of the behavior described here. They are implementation contracts, not evidence that the worker or Deltahub endpoints already exist. Contract changes must keep the schemas, detailed rules and examples consistent. JSON Schema validates structure. The semantic checks below remain mandatory application logic.

## Invocation and immutable input

Deltahub creates a private GCS payload object and launches one Cloud Run task with these non-secret bootstrap values:

| Value | Meaning |
| --- | --- |
| `job_id` | Current Deltahub job record; new on a later retry |
| `request_id` | Immutable request identity, checked against the downloaded payload |
| `job_lineage` | Original job ID and nullable immediate retry-predecessor job ID |
| `payload_uri` | GCS object containing `review-request.schema.json` |
| `payload_generation` | Exact object generation to read |

The worker uses its configured GCP service identity. Do not supply the JSON itself, OAuth tokens, `.env` secrets, or GitHub credentials through ordinary execution argument strings. Read the specific object generation and fail if unavailable; never silently fetch a replacement generation.

The non-secret bootstrap envelope is described by `job-invocation.schema.json`; it is separate from the immutable review payload. Original and retry jobs can point to the exact same payload generation. The worker records both invocation and request identities.

The payload includes the invocation mode, review identity, GitHub target, Jira and PR context, historical findings/report references, project setup/rules, prompt configuration, model choices, operational limits, permitted read scope, secret references, and artifact destination. The deployment config owns trusted Deltahub endpoint origins and GCP permissions; a payload must not redirect credentials to an arbitrary URL.

## Identities

| Identifier | Scope and behavior |
| --- | --- |
| `job_id` | One Deltahub job record; a later retry creates a new linked record |
| `review_id` | A logical code review for an immutable review input; discussion revises it |
| `request_id` | One immutable review or discussion request; reuse for an exact retry |
| `execution_id` | One Cloud Run execution launched for the current Deltahub job |
| `attempt_id` | One worker process attempt; one per execution with platform retries disabled; distinct from agent-stage attempt counts |
| `input_sha256` | SHA-256 of the exact downloaded payload bytes, calculated by the worker |
| `report_revision` | Monotonically increasing report version within `review_id`; can reflect assessment or delivery updates |
| `finding_id` | Worker-generated globally unique `finding-<UUIDv4>`; never recycled; preserved across reviews and checked against repository/PR for commands |
| `candidate_id` | Canonical candidate within one computation |
| `event_id` | Idempotency key for one callback event |

Store repository identity, PR number, head SHA, base SHA, base branch/ref, and resolved merge-base SHA. PR scope is the change from the merge base of the supplied head/base to the supplied head, rather than arbitrary changes already present on the target branch. Preserve the base tree as context. If the request supplies a merge-base SHA, verify it; otherwise compute and persist it before triage. Missing Git history must be fetched before deciding the relationship. An ambiguous/unrecoverable comparison fails explicitly.

`request_id` identifies the immutable review/discussion instructions across linked retry jobs. Job/execution/attempt IDs, retry linkage and launch time belong to the invocation envelope/checkpoints, not the immutable payload. A quota retry therefore changes job identity without changing payload bytes. The first job has `original_job_id == job_id` and null `retry_of_job_id`; later jobs retain the original ID and name their immediate predecessor. Callbacks/reports identify the current job; reused artifacts retain their producing job/stage provenance.

Use the immutable request identity, exact payload digest and stage configuration/runtime/prompt versions for checkpoint reuse. New head/base, requirements, prompts, rules, or review configuration are changed inputs, not exact retries. Credential values and their refresh are operational state, not review inputs. Credential references may use an authorized rotating version alias; rotation alone is not a code-review input change. Never include credential values in fingerprints or reports.

A completed baseline report may be supplied for follow-up; a failed review is not a completed baseline. For discussion, `review_id`, reviewed target, previous report object generation, and expected report revision identify the result being revised.

## Configuration

The request's project configuration contains:

- Setup recipe: expected Python/runtime profile, installation commands, preparation commands, and development-only environment secret references.
- Review rules: mandatory lenses with stable IDs, versions, and instructions; custom rules with unique IDs; tests/fixtures path patterns for size calculations.
- Model policy: fixed stage settings and the reviewer model/effort allowlist.
- Prompts: a pinned app-owned `prompt_bundle_version` and optional per-role replacements/additions in `prompt_customizations`; no replacement for mandatory policy. Reviewer assignments add lens-specific instructions.
- Limits: reviewers, concurrent agents, additional stage attempts, role-specific per-attempt timeouts, cumulative quota wait, total deadline, and finalization reserve.
- GitHub command handle: the exact configured text preceding `/dismiss`, such as `@hubbot`.
- Read permissions: allowed repositories, Jira projects, Deltahub projects, and public-web mode.

Defaults are 4 reviewers, 2 concurrent agents, 2 additional stage attempts, 1,800 seconds cumulative quota wait, and 7,200 seconds total execution time. A positive finalization reserve must fit within the total deadline; its value is deployment configuration, not a newly agreed product timeout. The code enforces these settings even if prompts request otherwise.

The proposed effort field is a string selected from configuration and validated against the pinned runtime/account. Do not assume all models support the same effort names. Exact model IDs and runtime pins are deployment choices to establish during the feasibility checks.

## Context and lazy reads

The request supplies the authoritative ticket and PR association; the worker does not search titles to resolve this association. `context.pr` carries repository/number, title, description, authenticated author, open/closed/merged state, and draft status. `context.jira_ticket` carries the authoritative key, title, description, and typed comments. `reviews` carries each review ID, author, state, reviewed commit, body, and submission time. `review_threads` carries thread/review IDs, resolved/outdated state, and typed comments. `pr_comments` carries non-inline discussion. Every comment has an ID, authenticated author, timestamps, URL, source ID, and explicit nullable parent/review/thread IDs. Do not hide these core fields in free-form metadata.

Context documents additionally provide source IDs, explicit `system` and `type`, URI, text, observation time, and optional authenticated actor metadata. Each typed entity's `source_id` must resolve to exactly one source record in `context.sources` (metadata only) or `context.documents[].source`; a document is not required, and PR/ticket URI and observation time come from that resolved source record. Text must agree when supplied in both places. `context.sources` may be empty when document sources supply all records; duplicate source IDs across the two collections are rejected. Filtered stage projections retain source records for every included typed entity. This adds a metadata-only index without requiring the optional removal of duplicated text. Optional metadata is for extensions, not required history. Validate the PR identity against `target`, unique IDs, referential integrity, reply parent relationships, and actor identity. Derive `is_pr_author` from the authenticated PR author ID, not names or comment text. A referenced parent outside a filtered agent projection remains explicitly retrievable; a missing required history page is not an empty history. Jira attachments may be represented by ID, name, MIME type, size when known, and retrieval reference without embedding their contents.

Agents can fetch allowed related tickets, PRs, comments, and attachments. Record the source, retrieval time, content digest, and the material used in the report's context/artifact manifest. Preserve fetched evidence used by a completed stage so retry does not silently replace it. If a fresh lookup changes an unfinished stage's evidence, record the new observation. Input immutability describes the supplied snapshot; it does not falsely claim that external systems stop changing.

GitHub mirrors and Jira projects explicitly permitted by the read scope can be searched. Pagination must be handled; never describe a truncated list as complete. Attachment size/type limits are operational configuration, with clear reports of omitted or unreadable material. Do not claim to have interpreted an unsupported attachment. A missing attachment is a capability limitation; a particular candidate requiring it may be unverifiable.

Public web search must avoid exposing private code, credentials, or internal ticket text in queries. Use abstract technical descriptions where possible. Credentialed attachment fetching must validate the destination and redirects rather than forwarding credentials to arbitrary links.

## Frozen authoritative requirements and change notifications

The payload's Jira description, supplied comments/clarifications, configured rules and any explicitly pinned authoritative requirement artifacts define the requirement snapshot for this request. Recent clarifications within that snapshot retain their agreed precedence. All stages and exact-input retries use the same authoritative snapshot. Lazy reads may add supporting evidence, but cannot replace these requirements. A changed source may explain why another review is needed; it is not a new requirement for the current verdict. Where the original authoritative content is required but unavailable, use required-context failure rather than substituting live text.

When a live lookup observes a material change to an authoritative source, checkpoint authoritative_context_change with original source identity/digest, the new observed source and immutable evidence artifact, and a concrete explanation. Return the frozen content for normative evaluation and label the new observation as a change notice. Continue the current review; do not rerun completed stages against the new requirements or let the verifier reinterpret their scope. New external technical evidence about an existing requirement remains eligible for ordinary investigation.

Emit authoritative_context_changed through the durable outbox and retain context_changes in every subsequent report, including failures and delivery retries. Notify Deltahub that a new code-review request (mode review, with a new review identity and the updated requirement snapshot) is required, even if the commit is unchanged; a targeted discussion alone does not review newly added requirements. The worker does not schedule it. The Check/overview explains which snapshot was reviewed and notes any observed change. Deltahub must not use that result to satisfy a gate for a changed requirement/configuration input even when the commit is unchanged. A drift notice does not change the current review's technical verdict. No polling for future Jira edits is implied; only observed changes are reported. Deduplicate notices by original source and observed content digest.

## Agent inputs and outputs

The worker creates six typed stage projections: history-import, triage, reviewer, aggregate, verifier, and discussion. See [agent-inputs-and-tools.md](agent-inputs-and-tools.md) for their schema links, context selection, and logical tool inventory. Agents never receive the complete worker request or its credential/delivery configuration. Agent outputs use one maintained simple structural schema per role, with required nullable fields where appropriate and Python validation for conditional/input-dependent rules. Local references are mechanically bundled before supplying the schema to Codex; no second hand-maintained schema or general schema conversion is used. See [schema-validation.md](schema-validation.md) and the [prompt bundle](../prompts/README.md).

| Schema | Purpose |
| --- | --- |
| `history-import-output.schema.json` | Structured human assertions and explicit no-finding decisions per authenticated source unit; code stamps origin |
| `triage-output.schema.json` | Proposed assignments, selected mandatory lens IDs, and rationale |
| `reviewer-output.schema.json` | Successful reviewer output, including an empty findings list |
| `aggregate-output.schema.json` | Input-ID groups; merged text only for actual duplicates |
| `verifier-output.schema.json` | Independent candidate assessments, required closed-finding checks, and final replies in both modes |
| `discussion-output.schema.json` | Proposed technical reassessments, evidence and draft replies, subject to independent verification |

Application code computes `review_context` (change statistics, review kind, baseline choice/fallback reason), assigns reviewer IDs, resolves mandatory lens definitions and prompt versions, and stamps source commit hashes. These fields are not agent output. Agents use local candidate selectors for cross-references and revision roles for code locations; code maps them to the execution namespace and fixed SHA values. `head` maps to `head_sha`, `base` to `base_sha`, and `merge_base` to `merge_base_sha`; the diff left side is the merge base, not necessarily the base tip. Evidence may cite the base tip, but it is not automatically a valid diff anchor. Unknown roles, conflicting selectors, or invented identities fail validation. New reviewer discoveries are stamped as AI-originated; the history-import stage interprets human assertions, while authenticated source mappings supply human authorship and source references. Agents do not output an origin/actor claim. Application code assigns/tracks IDs and stamps provenance. Do not rely solely on an agent's self-reported role, actor identity, completion status, or policy compliance. Successful runtime completion plus schema validation plus semantic validation are all required.

Semantic checks include:

- Reviewer IDs and candidate/source IDs are unique and refer to known records.
- Every mandatory lens ID resolves to its configured instructions/version, is assigned, and is retained in resolved assignment provenance. Every model/effort is allowed.
- At least one quality owner completes all named built-ins and exactly the configured custom-rule ID set; non-owners return null. Enforce rule severity mappings and known candidate references.
- All candidates derive from raw or known historical findings; aggregation does not invent findings.
- Each input in the new-plus-seeded-history candidate pool occurs once in a group; singletons are unchanged, and real merges preserve source evidence/provenance. Every required history ledger assessment is present regardless of reviewer discoveries.
- All candidates requiring assessment receive an assessment for this computation; retained dismissed/fixed history keeps its prior result. No candidate is verified twice in conflicting batches.
- Unverifiable assessments specify missing evidence and how to settle the question. Invalid assessments require an allowed invalid reason; others require null.
- Discussion proposals never become final technical assessments without a separate verifier result; fixed-state evidence pertains to the exact reviewed snapshot.
- Only code-validated explicit commands create human dismissals; natural-language arguments are technical discussion, not authority.
- Published suggestion text matches the replacement actually assessed.
- In both modes, dismissals have authenticated non-author human source comments identifying the exact finding. Code derives lifecycle actions from verifier results in both modes; replies target existing AI threads, and unresolved disputes cannot disappear through omission.
- Findings retained from a previous report keep their history and are not counted as new discoveries.
- Verdict and statistics match the report contents; the agent cannot choose the final verdict.

## Human import coverage contracts

Quality-owner reviewer inputs require an explicit import_accounting object conforming to import-accounting.schema.json. It carries every selected unit and zero-finding explanation, complete extracted assertions, stable worker-owned bindings and correction history. Non-owners receive null. Quality outputs require import_accounting_revision and import_omissions; an empty omission array and acknowledgment of the current revision are prerequisites for owner completion, not merely optional commentary.

History-import inputs have correction=null initially, or a bounded correction request containing the prior accounting and sourced omissions. Outputs always contain omission_resolutions: empty initially, exact omission coverage during correction. Imported/already-represented resolutions point to candidate IDs in the relevant source unit; not-an-assertion resolutions require an explanation and no candidate IDs. Preserve prior assertions/bindings and authenticate new human provenance in code. Reports retain an immutable import_accounting artifact; completed review-mode reports require it, including explicit empty accounting when there is no import work. Artifact content, ledger agreement and the owner's final acknowledgment are required semantic checks. See the [workflow](agent-workflow.md#import-accounting-and-omission-correction) for bounded correction and recovery.

## Discussion and closure contracts

Discussion requests require triggering `comment_source_ids`, not a pre-parsed nonempty finding list. Optional `finding_ids` may be omitted or empty. The worker resolves and checkpoints targets before applying changes as specified in [the workflow](agent-workflow.md#resolving-discussion-targets). Target IDs in worker-built discussion inputs remain required because resolution precedes agent execution.

`discussion-output` contains provisional reassessments, each with draft_replies, and closed-finding decisions when applicable. It does not produce authoritative actions. verifier-input.purpose distinguishes review and discussion; both modes use assessments, final_replies and closure_assessments from the independent verifier. assessment_bindings joins stable historical finding IDs to current candidate IDs; final_reply_targets specifies the exact AI conversation replies required. In review mode proposed_reassessments is empty and reviewer discoveries, original assertions and authenticated rebuttals provide the evidence to investigate. Unused output arrays are empty. Code derives accepted action records, applies validated human dismissals, and calculates the verdict in both modes. There is no reconciliation agent or verification loop after the verifier. The persisted finding_action.proposed_replies field contains accepted final replies, not provisional discussion drafts.

The quality owner's `closed_finding_decisions` covers each fixed/dismissed history entry exactly once, even when no new issues are discovered. The verifier independently checks changed circumstances for every closed finding included for reassessment or a required technical reply, including a `retain_closure` proposal; those `closure_assessments` are preserved in reports. Retained closed entries do not enter the candidate pool solely because they share a changed file. Unknown/missing/duplicate IDs, missing reassessment evidence and attempts to reactivate without verified relevant changes fail semantic validation. A valid technical assertion alone does not override a human dismissal.

Jira credential fields select service-account OAuth client credentials: `jira_auth`, `jira_cloud_id`, and `jira_credential_ref`. The reference points to the client ID/secret pair; no temporary access token is passed or stored in the review input. Local stdio MCP is the selected agent read-tool transport. See [agent inputs and tools](agent-inputs-and-tools.md#selected-transport-and-authentication).

## Reports and artifacts

`review-report.schema.json` represents a report revision. It contains code identity, execution/review status, triage, stage records, raw findings, canonical findings, verification and lifecycle history, prior-comment references, limitations, statistics, prompt/config/runtime provenance, and publication records. A completed report requires the resolved merge base; a checkout failure can report only the supplied target because no comparison was possible. A payload that cannot be parsed may have only a failure event, rather than a fabricated report.

Raw findings and canonical findings are separate collections. A canonical finding contains `source_input_ids`, stable finding identity, assessment, lifecycle, and history. Source inputs resolve to this computation's raw records or `history:<finding_id>` in the persisted `history_ledger`; original ledger coordinates retain their original SHAs until a new assessment supplies current evidence. No historical line is blindly relabeled as belonging to a newer head. Retained findings keep baseline provenance, and discussion revisions retain the original discovery records/counts. The report also stores resolved assignments, worker-computed review context, and accepted lifecycle/reply actions. A failure before comparison may have null review context. An authoritative dismissal does not overwrite the original verification evidence. For accepted disagreement, preserve the invalidation evidence and the reply acknowledging it.

Save immutable report revisions. Mutable pointers such as a latest-report index are conveniences, updated with generation/revision preconditions; they are not the authoritative artifact. A report can carry a null verdict when computation failed, with completed reviewer outputs and pending candidates preserved. A completed assessment can carry an approved/requires-changes verdict while execution failed or stopped during delivery. `execution_status` is separate from `review_status`: the latter is `completed`, `failed`, or `stopped` (stopped before computation completed). `stop` records known stop/cleanup information. Deltahub records abrupt job failures even when no report can be saved. `revision_reason` identifies `initial`, `discussion`, `delivery_update`, or `execution_retry` revisions. `failure` represents computation failure; `delivery_failure` separately carries a typed operational failure after completed computation, without changing the verdict. A completed review with failed execution requires the latter. A stopped execution uses `stop`, not a fabricated delivery failure.

Detailed logs and fetched attachments live in separate artifacts referenced by the report. Exclude secrets, `.env` contents, authorization headers, and unredacted credential-bearing URLs. Store observable stage outputs/tool evidence and runtime-provided usage, not an assumed transcript of hidden model reasoning. Unknown usage is null/absent, not zero. Quota percentages are not a monetary bill.

Checkpoint the completed computation and publication intent first, **publish to GitHub before saving the final report**, then save an immutable report revision containing publication IDs and status. No numbered pre-publication report is required. If publication fails, save the same assessment with actual failed/partial publication details. If stopped after computation, save the result when possible with stopped execution and actual delivery progress. Incremental checkpoints, not a final signal handler, provide crash recovery.

If a later linked retry completes delivery after a failed-publication report was saved, write a new immutable report revision with `revision_reason: delivery_update`, current execution/job identity and updated publication results. Do not rerun compatible completed agents or alter the assessment merely because delivery changed. There is no separate final delivery report. Stage/publication/outbox checkpoints remain normal recovery artifacts, not a competing report model.

Reserve the intended report revision under integration concurrency control before publishing and checkpoint it with the publication plan. GitHub markers refer to that reserved revision even though the final JSON is saved afterward. On a crash after a successful write, the retry reconciles markers/IDs and the reserved revision before writing again. A retry of a saved failed-delivery revision reserves the next revision; it cannot reuse that immutable report path. New discussion requests reference the latest saved revision and use an expected-revision precondition; exact-input retries follow the same-request lineage exception in the reservation protocol below. If publication/revision state advanced, fail/reconcile the stale request rather than silently replacing its immutable input. Never let older publication overwrite newer review content.

Send the durable report revision and reference in the final Deltahub event. Reports do not contain acknowledgment of the callback carrying themselves; acknowledgment remains a checkpoint. A failed callback can be retried from that checkpoint without fabricating another assessment or requiring another report revision unless report metadata actually changes.

## Revision reservation and retry completion

One integration-configured GCS coordination object per `review_id` stores `report-coordination.schema.json`: the last saved revision, nullable last completed assessment revision, nullable active reservation, and nullable recovery claim. Its location is stable across code-review, discussion and retry requests; do not derive a separate lock from each request/job output directory. Trusted integration configuration supplies the coordination prefix, and the worker has access only to its authorized review records. The reservation contains its ID, request/job/execution owner, next report revision, expected prior revision and immutable report URI. Reports include this `reservation`; its identities and revision must match the report.

Before the first GitHub write or any terminal report save, acquire the reservation with a conditional GCS write: create with `ifGenerationMatch=0`, or update the generation just read. With no active reservation, allocate `last_saved_revision + 1`. Expected prior revision is null only when no report has been saved (last_saved_revision 0); otherwise it is the exact last saved revision. A competing live reservation prevents publication; return `revision_conflict` rather than proceeding. A newly launched discussion additionally requires its immutable expected revision to equal the current saved revision. Its previous_report identifies the latest completed assessment revision, which can be earlier than that saved revision after a failed/stopped discussion. An authorized exact-input retry may have intervening failed/stopped/delivery revisions produced by that same request and retry lineage; it retains the original discussion input, reserves after the actual last saved revision, and reuses its checkpoints. Reject this exception if any intervening revision belongs to a different request or changes the assessment outside that retry chain. This serializes writes for the logical review, including early Check registration, without introducing a second final report.

Conditional writes use [Cloud Storage generation preconditions](https://docs.cloud.google.com/storage/docs/request-preconditions). If reservation acquisition fails or ownership cannot be established, emit a failure-only event and preserve job-scoped checkpoints; do not write an unreserved report into another owner's revision.

A linked retry may take over a dead predecessor's active reservation using compare-and-swap only after the integration confirms that predecessor execution is terminal and the retry lineage is authorized. Elapsed time alone is not proof of termination. If no report was saved at its reserved URI, preserve that revision, reconcile remote writes, and replace owner identity with the retry's job/execution; persist the old ownership in recovery artifacts. If the report was already saved, verify its identity/digest and finalize the saved-revision pointer before allocating any later revision. Advance last_completed_revision only for completed computations; a failed/stopped computation does not erase the prior completed assessment. Save reports with create-only preconditions; never overwrite an existing report. Release the reservation and advance last_saved_revision using the generation held; an ambiguous acknowledgment requires reading and reconciling the object, never a blind increment. A saved report is authoritative if the pointer update was interrupted.

A failed or stopped computation can save revision 1; an explicitly scheduled later retry that completes computation saves revision 2 with `revision_reason: execution_retry`. The same rule applies to any later revision number. Intentional stop still does not schedule a retry automatically. If a saved completed computation only needs delivery recovery, use `delivery_update`. A discussion's first saved outcome uses `discussion`; a retry completing its failed computation uses `execution_retry`. Without any previously saved report, a resumed initial review still saves revision 1 as `initial` (a discussion retains `discussion`). A further failed retry also advances the revision when its predecessor report was saved. Each revision keeps prior reports intact.

Final events carry the reservation's expected prior revision, not always null. Deltahub atomically accepts the expected predecessor, or acknowledges an exact already-accepted duplicate. Intermediate failed/stopped revisions must be registered in order if their callbacks were delayed; a new revision must not skip reconciliation of its predecessor. Same-attempt callback retries reuse the saved report/outbox event. If a later job writes a report with its own execution identity after a callback-only failure, it is a new `delivery_update` revision; do not rewrite the old report merely to change its job ID.

## Abandoned reservation cleanup without resuming the request

A new request is not required to retry a stopped or abandoned computation to unblock its logical review. A trusted worker may perform bounded reservation cleanup before its own request starts, under explicit Deltahub recovery authorization. This is an operational recovery path, not a new agent mode or automatic resumption after stop. Authorization identifies the review, abandoned reservation, predecessor job/execution and authorized recovery job/execution. Independently confirm that the predecessor is terminal using platform evidence and reconcile Deltahub's recorded stop intent; elapsed time alone is insufficient.

Claim cleanup by conditional update of the coordination object's recovery field, leaving active_reservation and its original report identity intact. Persist the claim/evidence as a reservation-recovery checkpoint before any remote reconciliation. Normal publishers and retries must refuse a reservation with an active recovery claim. Only the current recovery owner may advance it; takeover of a crashed recovery owner also requires terminal evidence, authorization and compare-and-swap. An authorized linked retry of the original computation remains the existing alternative, but cannot run concurrently with cleanup.

Read the predecessor's checkpoints, reserved report URI and GitHub markers. If the immutable report already exists, verify it and finish its pointer update. Otherwise save the predecessor's terminal report at its reserved revision, using its original request/job/execution/reservation identities: stopped when confirmed intentional, otherwise failed with execution_lost or the known failure. Preserve already completed computation and its verdict if established by a durable checkpoint; never infer completion from missing work. Record actual publication progress and retain all accepted dismissal records, even when no new overall verdict was issued. The separate recovery checkpoint identifies who performed cleanup; do not pretend that its job ran the original agents.

Cleanup reconciles existing remote writes and may close only an abandoned in-progress Check under the established ownership guards. It does not restart agents, finish stopped publication, delete human comments, overwrite completed Checks, or fabricate missing GitHub acknowledgments. Preserve acknowledged bot objects and ambiguous operations in the checkpoint for subsequent publication reconciliation. Only after the terminal report is durably saved (or an existing report verified), finalize last_saved_revision, preserve/update last_completed_revision, and clear active_reservation and recovery in one conditional update. Storage/auth failures leave recoverable cleanup pending rather than silently dropping the reservation.

Queue the original job's terminal report event through its durable, sequence-controlled outbox under recovery authorization. Delivery of that event can retry independently after the reservation is cleared. The recovery checkpoint records completion and terminal report/publication references using reservation-recovery.schema.json. A later discussion uses the latest completed report as its assessment baseline and the latest saved revision as its write precondition. If cleanup advanced the saved revision beyond the new request's immutable expected value, return an actionable revision_conflict with the current pointers; Deltahub creates a fresh request. This may require a refreshed payload, but never an unwanted retry of the abandoned computation.

## Deltahub API operations

The following operation names define required behavior. Exact URL paths and backend models remain implementation details owned by Deltahub.

| Operation | Contract |
| --- | --- |
| Obtain/refresh account credentials | Authenticate the worker, identify the permitted account reference, return fresh credentials securely; Deltahub serializes renewal of shared credentials |
| Read job control / authorize reservation recovery | Authenticate the worker; return recorded stop intent and authorized predecessor/recovery identities. Recovery authorization is issued by trusted Deltahub control logic, never inferred from agent text or an untrusted payload |
| Submit progress event | Accept `job-event.schema.json`; deduplicate by `event_id`; enforce attempt and sequence ordering |
| Submit final result | Accept the same event envelope with the complete report and immutable GCS reference/digest |

Use authenticated HTTPS. The deployment must define how worker identity is verified by Deltahub; do not embed a permanent backend token in review prompts. Retry transient delivery failures with bounded backoff and respect server retry instructions.

`sequence` is monotonic within the current job/attempt. Deltahub deduplicates updates to that job and retains retry linkage; a larger sequence from a predecessor job cannot replace the successor's state or review publication. Platform task-restart ordering is unnecessary with `max_retries = 0`, but late callbacks from prior jobs still require identity/revision checks. Final result revisions require an expected prior revision or equivalent concurrency check. A duplicated accepted event returns acknowledgment without repeating effects. The backend must reject/report revision conflicts instead of silently accepting stale updates.

Every completion event identifies the exact reviewed input. The backend must never apply it to a different gate merely because it is the latest callback received. Serialize or use revision checks for overlapping review/discussion publications on the same logical review. Cross-job scheduling and account-wide concurrency remain Deltahub responsibilities; the worker's limit of two agents is per instance.

## Progress event kinds

Every event uses the same identity/sequence/idempotency envelope. These meanings apply equally to review and discussion invocations. Events are durable outbox records; absence of an acknowledgment means delivery is pending, not that the computation should repeat.

| `kind` | Meaning and required data |
| --- | --- |
| `check_registered` | Check creation/reconciliation is durably recorded; requires `check` identity and checkpoint, with null report/reference |
| `authoritative_context_changed` | A changed authoritative source was observed and durably recorded. Requires context_change and checkpoint, with null report/reference. Continue using the supplied snapshot; Deltahub schedules a new request |
| `started` | This worker attempt has begun. No verdict is implied; `stage_id` may be null |
| `stage_started` | A named stage attempt is beginning; requires `stage_id` |
| `stage_completed` | A named stage completed successfully and its output checkpoint was persisted; requires `stage_id`. An empty valid reviewer output qualifies |
| `stage_failed` | A named stage attempt failed; requires `stage_id` and `failure`. It is not a terminal job event: retries may remain |
| `waiting_for_quota` | Execution is pausing within its allowance. Requires `quota_wait` with nullable reset time, cumulative waited seconds, and remaining allowance; no review verdict implied |
| `review_completed` | All required computation and composition succeeded. Requires an immutable computation `checkpoint`; `report` and `report_artifact` are null. GitHub publication and final report creation are next |
| `delivery_failed` | Computation succeeded, but GitHub publication or result delivery failed. Requires delivery failure plus either the saved completed report/reference or, when final report storage failed, the durable computation checkpoint with null report/reference. Preserve the computed verdict; delivery recovery can continue |
| `finished` | Computation and required GitHub publication/reconciliation succeeded, and this is the final result awaiting Deltahub acknowledgment. Requires a completed report with publication `complete` and its artifact reference |
| `failed` | Computation ended without a new verdict. Requires a failure; report/reference may be null when no report could be produced. Any supplied report is failed with null verdict |
| `stopped` | Known intentional stop; requires `stop` details. Optional report preserves completed computation if available, otherwise has stopped computation and null verdict. No automatic retry |

`review_completed` precedes publication completion; `finished` records the deliverable result. Acceptance of `finished` acknowledges final delivery in the outbox/checkpoint, not inside the report being delivered. A Deltahub outage cannot reliably announce itself over the failed connection: persist the event/failure and let retry or backend reconciliation deliver it later. Never emit computation `failed` solely because delivery of a completed review failed.

Failure is non-null only for `stage_failed`, `failed`, or `delivery_failed`; quota details are non-null only for `waiting_for_quota`. Stage failures must name the same stage in the envelope and failure. A report and report artifact are supplied together or both null, with matching digest, identity and revision. Only authoritative_context_changed carries non-null context_change; only `stopped` carries non-null stop details; a platform SIGTERM without recorded stop intent is not automatically classified as stopped. For a linked retry job, checkpoint reuse can mean not re-emitting earlier computation events; persist the references and emit only the transitions that actually occur. Do not restart sequence numbering within an attempt or interpret a later event from an obsolete attempt as current.

## Early Check registration and delivery diagnostics

Immediately after creating or reconciling a Check, checkpoint its identity and enqueue `check_registered` before computational stages continue. This event carries `check` (GitHub ID/URL, repository, PR, reviewed head/base, review ID and current owning job/execution) and the durable checkpoint reference; it needs no report. Retry workers emit registration for the reconciled Check under the new owner. Deltahub records the latest authorized ownership and guards cleanup against it; an old job's failure must not close a successor's Check. A worker can still die between the remote write and checkpoint/event; deterministic publication markers and recovery handle that unavoidable gap. No final callback is guaranteed.

`delivery_failure` uses the existing closed failure vocabulary and retry guidance, with stage and retained artifacts. Completed-review reports with failed execution must contain it; computation failures keep it null. Publication object error strings provide local detail, not the sole machine-readable failure. `delivery_failed` events carry matching typed failure details and the saved report/reference when the report already records that failure. A newly observed callback failure may instead reference the already-saved completed report with null delivery_failure; in that case the event failure is deltahub_delivery_failed and the durable outbox supplies the later observation. Callback failure discovered after saving a report stays in the durable outbox/checkpoint; do not recursively rewrite a report to record failure delivering itself. If a subsequent report is saved, include the then-known delivery state under the revision rules above.

## Failure and acknowledgment semantics

The failure envelope identifies the stage, reason, retryability, optional earliest retry time, and retained artifact references. A complete review with failed publication is different from failed computation. A callback outage does not invalidate the computed verdict or delete its report.

An abrupt container loss may prevent a final callback. Deltahub observes terminal execution state, records job failure/stop and arranges a linked retry as appropriate. It need not inspect the review's progress; the next worker reconciles durable artifacts and remote writes. Absence of a callback is never approval, and a final callback cannot be guaranteed. This is an integration requirement, not a new worker trigger.

## Storage failure after completed computation

If final report storage fails after a durable computation checkpoint, delivery_failed may carry report=null and report_artifact=null, failure.code=artifact_io_failed, and that checkpoint. Include known publication operations in retained durable artifacts; never supply a planned report URI as if upload succeeded. This event reports execution/delivery failure without reclassifying completed computation. Deltahub records failure and schedules recovery; it must not treat a checkpoint-only event as final gate approval. Recovery reconciles publication and saves the report without rerunning compatible agents. Normal finished events still require a saved completed report. If no durable computation checkpoint exists, computation has not met the completion contract and follows the ordinary failed path.

## Failure codes and retry guidance

`failure.code` is a closed v0.1 vocabulary. `retryable` means an exact-input retry may be useful after the stated condition clears; it is not permission for immediate unbounded platform retries. Deltahub uses code, retryability, `retry_not_before`, and execution history together. Cloud Run automatic task retries are disabled; Deltahub owns later job retries.

| Code | Meaning and retry guidance |
| --- | --- |
| `invalid_input` | Malformed/inconsistent request or forbidden values; not retryable unchanged |
| `unsupported_configuration` | Unknown/incompatible model, runtime profile, or impossible required coverage; correct configuration first |
| `revision_unavailable` | Required exact Git object/comparison unavailable; retry only when recoverable without substituting revisions |
| `repository_access_denied` | Repository access missing; intervention required, not automatic retry unchanged |
| `context_unavailable` | Required context unavailable; retryable only for a transient retrieval failure. Optional missing context is a limitation |
| `setup_failed` | Setup attempt failed. Readable source continues with a limitation; it is not terminal merely because execution is unavailable. Retryability depends on the recorded cause |
| `authentication_required` | Account revoked or interactive login required; intervention first |
| `credential_refresh_failed` | Renewal failed; retryable for a transient service error, otherwise intervention |
| `upstream_unavailable` | Temporary SDK/provider/read-service failure; bounded retry |
| `stage_output_invalid` | A returned result failed structural or semantic validation; consumes a stage attempt, with bounded retry |
| `stage_timeout` | One agent attempt exceeded its configured role work allowance; bounded retry if attempts and overall execution time remain |
| `stage_attempts_exhausted` | Required computation did not produce usable output within its allowance; later retry may reuse completed stages, but no immediate retry loop |
| `quota_exhausted` | Account cannot resume within remaining allowance/deadline; retry later. Populate `retry_not_before` when a usable reset time is known |
| `execution_lost` | Confirmed terminal worker loss without a final worker report; recovery preserves durable progress and records operational failure, with no invented completed computation |
| `execution_timeout` | Worker computation deadline exhausted; later retry can reuse compatible durable work |
| `sandbox_unavailable` | Required execution/access boundary cannot be enforced; intervention/configuration change, not unrestricted execution |
| `artifact_io_failed` | Required artifact could not be saved/read/verified; transient I/O can retry, digest mismatch requires investigation |
| `github_access_denied` | Publication permission/access lost; preserve computed report, intervention first |
| `github_delivery_failed` | Other GitHub publication failure after reconciliation; transient errors retry delivery only, permanent validation errors require correction |
| `deltahub_delivery_failed` | Callback delivery failed; persist outbox/report. Transient errors retry delivery only; rejected authorization/data needs intervention |
| `revision_conflict` | Expected revision/attempt no longer current; reconcile before any retry, never overwrite the newer result |

`retry_not_before` is null when no reliable earliest time is known; it is not an instruction to retry immediately. For non-retryable errors it is null. Human-readable messages explain the specific cause but never replace the stable code used by the backend. SDK/provider error details, when useful, belong in redacted diagnostics rather than invented failure codes.

Every failure has `retained_artifacts`, an array of immutable URI/generation/digest references to completed work. It is empty when nothing was durably saved. This includes failure-only callbacks with null report, so recovery does not depend on having reached report composition. References must identify successfully stored objects, not planned uploads. No verdict is inferred from retained reviewer artifacts until all required stages succeed.

## Schemas and examples

Schemas use JSON Schema Draft 2020-12 and relative references. `common.schema.json` contains shared definitions. Schema IDs use the reserved `schemas.deltahub.invalid` domain solely as identifiers; resolve references from the local schema bundle, not the network. Examples use synthetic repositories, SHA values, models, secrets, and URLs; they are not deployment configuration. Each example is listed with its schema in `examples/manifest.json`.

Reject unsupported major schema versions. Changes to mandatory fields, verdict meaning, or identity matching require a versioned migration. Extensions must not silently change gate semantics.
