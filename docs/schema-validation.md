# Structural schemas and Python validation

Agent outputs have one maintained structural definition per role. They use objects, arrays, primitive types, enums, nullable values, `anyOf`, required properties, and references. Every object rejects extra properties and every declared field is required; inapplicable values are explicit null. Conditions and cross-field/input-dependent rules belong to Python validators. Requests, reports, inputs and events remain richer application contracts and may use Draft 2020-12 conditions.

Shared output types live in `common.schema.json`. [bundle_agent_schema.py](../scripts/bundle_agent_schema.py) only relocates local references into a self-contained `$defs` bundle. It does not remove constraints, change field shapes, or maintain a second contract. For example:

```sh
python3 scripts/bundle_agent_schema.py reviewer --output /tmp/reviewer-output.schema.json
```

The worker supplies that bundled schema to Codex. Verify support against the pinned SDK/runtime as part of implementation; local structural checks do not demonstrate a live Codex integration. Do not silently fall back to prose or weaken the contract if the runtime rejects the schema.

## Required validation sequence

A stage succeeds only after runtime completion, JSON/schema validation, Python semantic validation and durable checkpointing. Invalid output uses the existing bounded repair/attempt policy; it is never an empty successful review. The worker stamps trusted identities, commit hashes, authorship and prompt provenance rather than accepting agent assertions about them.

| Area | Required Python checks beyond structural validation |
| --- | --- |
| General | Nonempty meaningful strings where specified; unique known IDs; positive ordered line ranges; revision roles mapped to immutable source; actual files/locations and allowed tools/scope |
| Triage | Nonempty plan within cap; allowed model/effort pairs; all mandatory lenses resolved unchanged; complete quality ownership; worker-computed statistics/baseline facts stay authoritative |
| Reviewer | Unique local candidate IDs; required title/body/evidence; primary location null or included among evidence locations; existing IDs resolve to ledger; new discoveries stamped AI by code |
| Severity | Scope/requirements/language/internal-reference findings are major; custom-rule findings are blocking and reference configured rule IDs; technical findings follow the supplied rubric |
| Quality | Owners return all named built-ins and exactly one result per configured custom rule; non-owners return null; finding results reference known candidates/history; other results require specific explanations |
| Aggregation | Nonempty groups partition all supplied IDs exactly once; singleton has null merged text/rationale; multi-input groups have merged text/rationale and preserve evidence; historical identity and fixed severity mappings survive |
| Verification | Exactly one result for each required candidate; evidence on every assessment; invalid requires an allowed `invalid_reason`, other statuses require null; unverifiable requires missing evidence and a resolution description; suggestions match the exact patch assessed |
| Discussion | Proposals cover resolved technical targets and remain provisional; independent verifier returns complete assessments and final AI replies, then code applies lifecycle changes. No discussion reconciliation stage; no guessed/foreign targets |
| Closed history | Quality owner covers every fixed/dismissed entry exactly once; reassess needs specific change evidence. Independent closure assessment covers every selected closed finding; reactivation requires confirmed relevant change plus valid/unverifiable issue assessment |
| Lifecycle | Confirm requires valid, invalidate invalid, leave_unverifiable unverifiable, and mark_fixed invalid/fixed_in_reviewed_code. Reactivation needs relevant-change evidence and renewed valid/unverifiable action. Fixed-state evidence must establish a fix in the reviewed snapshot, not only a later commit |
| Dismissal | Agent schemas cannot emit `dismiss_by_human`. Code validates exact configured command text outside quotes/code, authenticated non-author human identity, PR/finding scope and source uniqueness; keeps an immutable command audit record and acknowledges it without model agreement |
| Reports | Verdict/statistics agree with canonical findings; required computational stages succeeded; history/provenance and independent verification retained. Execution failure/stop is distinct from computed result. Reserved revision/publication IDs agree; delivery-only changes retain assessment |
| Retry identity | Invocation request ID matches payload; exact retry uses identical payload generation/digest but a new job/execution/attempt. Original/predecessor job links are correct; reused artifacts retain producing identities and compatible runtime/prompt fingerprints |
| Events | Matching job/request/review/revision identities; monotonic per-job sequence; paired report/reference and matching digest; review_completed has computation checkpoint and no final report; stopped reflects known intent, not SIGTERM alone |
| Prompts | Known pinned bundle; mandatory policy cannot be replaced; ordered role replacement/additions produce recorded exact text/digest; mandatory checklist/lens/rule coverage stays enforceable independently of prose |

A schema can therefore accept a structurally valid singleton with replacement text, or an invalid assessment with null reason; Python must reject it. This separation is intentional. A completed checklist is also not proof of a thorough investigation: representative quality evaluations remain necessary.

## Repository checks

The [pytest contract suite](../tests/contracts/test_examples.py), also available through the compatibility [validate_specs.py](../scripts/validate_specs.py) command, validates all schemas/examples, mechanically bundled output structures, prompt and artifact digests, representative semantic rules, and negative regression probes. Install the locked development and `specs` dependency groups as described in the [team guide](../CONTRIBUTING.md), then run:

```sh
uv run --locked --group specs python -m pytest tests/contracts
```

This is contract/example tooling, not the worker implementation. It exercises representative invariants but cannot validate actual repository coordinates, GitHub identity/permissions, deployment isolation, live SDK schema acceptance or the factual quality of evidence. Those remain implementation acceptance criteria in [acceptance.md](acceptance.md).

Additional required semantic checks cover exact human source-unit accounting, authenticated provenance stamping, candidate-count dispatch, candidate/finding bindings across computations, UUID allocation/PR membership, source-ID resolution and duplicate-text agreement, reservation ownership/revision transitions, typed delivery failures, early Check ownership, and synchronized thread links. Agent reply destinations are never accepted from generated URLs. The regression fixtures exercise these independently of any live deployment.

## Completion, bindings and reply coverage

Derive each finding/candidate binding from exactly one history:<finding_id> membership in the current canonical candidate's source_input_ids. Reject swapped known IDs, duplicate historical membership, conflicting mappings, unknown history, and references inconsistent with original source candidates. Verifier inputs include the relevant canonical candidates; code preserves the validated bindings when deriving lifecycle actions after verification. Do not validate only the two sets of identifiers.

Reports carry worker-owned required_stage_ids and a durable computation_plan reference. Check them against the checkpointed orchestration plan and resolved reviewer assignments. Required stage IDs are unique, present, and succeeded; successful computational stages have completion_artifact references. Reviewer stage IDs equal their resolved reviewer IDs. In review mode, require triage, every resolved reviewer, composition, deduplication when the candidate pool has at least two entries, and verification when the pool is nonempty. Additional required history-import/verifier-batch stages come from the plan. Reports retain worker-resolved technical_discussion_finding_ids independently of agent actions. In technical discussion require investigation, verification and composition; command-only discussion requires composition. No failed, stopped, running or pending computational stage can support a completed verdict; earlier failed attempts stay in attempt diagnostics rather than masquerading as additional current stage records.

A reused stage remains succeeded and carries reused_from with its producing job/execution/stage and completion artifact. Verify immutable bytes, successful producer outcome and input/runtime/prompt compatibility before accepting reuse. Its completion_artifact must match the referenced producer artifact. A missing artifact, incompatible input, unknown stage or claimed success without completed evidence is not valid reuse. Plan and artifact content checks are implementation requirements; synthetic examples demonstrate the contract without claiming remote fixtures exist.

Reply coverage is keyed by reply_target_id, not finding_id. Check target/source/finding mappings against the worker-owned routing table; several replies may share one finding. A retained closure must serialize through the same accepted-action/report path as other outcomes. Authoritative-context notices use the continue_snapshot policy and cannot silently revise agent requirements.

## Shared verification and separate import role

In both modes require exact candidate assessment coverage, exact reply-target coverage and independent closure checks for selected closed findings. Review-mode replies are valid and required when targets exist; code derives lifecycle actions from the same verified evidence used for the reply. The historical-binding, human-thread and routing restrictions apply identically. Reject removed reconciliation stage kinds, loop configuration and limit-exceeded failure codes. An actual verifier timeout/crash still fails the required stage after bounded retries.

History-import inputs resolve the history_import base prompt and only history_import customizations. Validate base prompt provenance against the stage as well as checking mandatory text and digests. models.history_import and its positive attempt timeout are required; discussion settings are independent.

## Import accounting and coverage repair

Validate unique complete source-unit accounting, including excluded/empty units; unique exact candidate-to-finding binding coverage; authenticated human provenance and retained original thread links in the ledger. Quality owners must receive accounting and acknowledge its current revision. Validate each omission's unit/comment membership, nonempty assertion/reason and unique ID. Pending omissions mean provisional reviewer output, never a completed quality-owner stage.

Correction output preserves all previously accepted assertions in affected units, returns no foreign units and resolves every requested omission exactly once. Imported IDs are new; already-represented IDs already exist in the same unit; non-assertion resolutions contain no candidate IDs. Validate the configured pass allowance and durable consumed budget before dispatch. The example validator checks successful accounting revisions and supplied bounds; production also checks pending/failed pass checkpoints so retries cannot reset consumed attempts. The refreshed owner must accept the new accounting before downstream stages. Validate report artifact contents and the accepted owner completion against the same final ledger; a mere artifact URI does not prove coverage.
