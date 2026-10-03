# v0.1 JSON contracts

These files describe interfaces, not an implemented service. Read [the contracts document](../docs/contracts.md) for identity, ordering and semantic requirements. These are the agreed, not-yet-deployed v0.1 implementation contracts.

| Schema | Producer → consumer |
| --- | --- |
| [job-invocation](job-invocation.schema.json) | Deltahub → worker bootstrap; per-job identity and retry lineage |
| [review-request](review-request.schema.json) | Deltahub → immutable request, reused across exact retry jobs |
| [history-import-output](history-import-output.schema.json) | Human-content interpreter → assertions per authenticated source unit; worker stamps provenance |
| [triage-output](triage-output.schema.json) | Triage agent → orchestrator |
| [reviewer-output](reviewer-output.schema.json) | Reviewer agent → orchestrator |
| [aggregate-output](aggregate-output.schema.json) | Deduplication agent → orchestrator |
| [verifier-output](verifier-output.schema.json) | Independent verifier → assessments, closed-finding change checks, and final replies in both modes |
| [discussion-output](discussion-output.schema.json) | Discussion investigator → provisional technical reassessments |
| [review-report](review-report.schema.json) | Worker → GCS/Deltahub, after publication or failure fallback |
| [job-event](job-event.schema.json) | Worker → Deltahub progress/results/stop |
| [report-coordination](report-coordination.schema.json) | Worker → conditional GCS reservation and saved-revision pointer |
| [common](common.schema.json) | Shared definitions |

Worker-created inputs are [history import](history-import-input.schema.json), [triage](triage-input.schema.json), [reviewer](reviewer-input.schema.json), [aggregate](aggregate-input.schema.json), [verifier](verifier-input.schema.json), and [discussion](discussion-input.schema.json). See [agent inputs and tools](../docs/agent-inputs-and-tools.md).

Application contracts use JSON Schema Draft 2020-12. Resolve references locally by `$id`; the reserved `.invalid` identifiers are not network services. Schema defaults document recommendations and are not automatically populated. Validate date-time formats explicitly. The [example manifest](../examples/manifest.json) declares each example's schema.

Agent outputs deliberately use simple supported-shape structures. Shared references are mechanically bundled with [bundle_agent_schema.py](../scripts/bundle_agent_schema.py); there is no general conversion layer or independently maintained alternate schema. Every field is required, with null for optional values. Conditional and input-dependent rules are enforced by Python as specified in [schema-validation.md](../docs/schema-validation.md). Validate both original and bundled schemas against examples; implementation must also exercise the pinned Codex runtime.

An agent's JSON does not establish successful runtime completion or correctness. Python validates exact checklist/rule coverage, singleton preservation, severity rules, verifier status/reason combinations, historical candidate completeness, command authority and verdict calculation. Richer persisted report types may include worker-owned data absent from agent outputs, such as commit hashes, actor provenance and accepted dismissal actions.

[reservation-recovery](reservation-recovery.schema.json) describes operational cleanup checkpoints for abandoned reservations. Coordination distinguishes last_saved_revision from last_completed_revision and records exclusive recovery ownership. Reports include a computation plan, required stages, per-conversation reply targets and observed authoritative-context changes; stage records explicitly identify reusable completion artifacts.

[import-accounting](import-accounting.schema.json) records full human-source coverage, extracted assertions, stable finding bindings and immutable correction history. Quality-owner reviewer inputs include it explicitly; reports reference its durable artifact. History-import correction input/output and quality-owner omission fields define the bounded repair protocol.
