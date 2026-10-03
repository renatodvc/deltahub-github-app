# Agent inputs and tools

The worker builds a stage-specific input after validating the request, resolving Git history, and loading required context. Inputs are logical data contracts; the selected tool transport is an app-owned local MCP adapter over stdio, with native runtime workspace and web tools. SDK message encoding and individual endpoint mappings remain implementation details. Agent outputs use simple structural schemas with mechanically bundled references and separate Python validation, as specified in [schema-validation.md](schema-validation.md). Verify the bundled shape against the pinned runtime during implementation.

## Shared context and worker-owned facts

Each input identifies the exact target, including its resolved merge base, and includes worker-computed `review_context`, typed PR/Jira context, mandatory lens definitions, custom rules, fixture patterns, the resolved app-owned/customized prompt with assembly provenance, allowed tool IDs, relevant history ledger entries, an artifact manifest, and an optional workspace descriptor. A workspace states whether setup succeeded or only source inspection is available. The input records what the agent actually received and is checkpointed before execution.

The worker retains bootstrap values, credential/secret references and values, callback configuration, publication permissions, and storage write authority. None is projected into an agent input. The development environment is materialized through controlled setup; its `.env` contents are not copied into prompts or manifests. Workspace/process isolation must enforce the runtime boundaries described in [runtime-and-recovery.md](runtime-and-recovery.md).

Give every stage the PR/ticket identity and requirement summary. Select detailed documents, threads, code/diff artifacts, and attachments according to its assignment. Keep source IDs and typed reply relationships. Do not silently summarize away a requirement or rebuttal relevant to the assigned work. Large documents and attachment bodies may remain retrievable references; include name/type/size and source identity. A projection may contain a subset of threads, but the worker's complete history ledger remains authoritative for coverage.

`review_context` contains facts computed by code: first/follow-up status, baseline ID/fallback reason, and raw/effective diff statistics. Resolved reviewer assignments include code-assigned identity, prompt reference, mandatory lens instructions/versions, and expected custom-rule IDs. Persist both the agent's triage proposal and the resolved assignments. Agents cannot change these facts by echoing different values.

## Stage projections

| Input contract | Required stage-specific material | Context selection and capabilities |
| --- | --- | --- |
| [History import](../schemas/history-import-input.schema.json) | Complete worker-selected human source units and authenticated context; nullable correction with prior accounting, omission batch and worker-owned allowance | Interpret asserted issues before ledger construction; scoped source/context reads, no publication; dedicated history_import prompt/model/timeout |
| [Triage](../schemas/triage-input.schema.json) | Reviewer model/effort choices, reviewer cap, diff/change inventory, mandatory lenses/rules, baseline/follow-up facts | PR/Jira requirements, setup limits, relevant history summary; read source/context to determine assignments |
| [Reviewer](../schemas/reviewer-input.schema.json) | One resolved assignment, assigned diff/source artifacts, complete checklist, explicit complete import_accounting and every closed finding with closure/comparison context if owner | Requirements and relevant threads/history; scoped reads, web, focused workspace execution |
| [Aggregate](../schemas/aggregate-input.schema.json) | Every new or seeded historical candidate under a worker-assigned input ID | Assertions, evidence/provenance and rubric; no tools or execution needed; groups IDs rather than rewriting singletons |
| [Verifier](../schemas/verifier-input.schema.json) | Canonical candidates and source input IDs, original source candidates, relevant history/rebuttals, provisional discussion reassessments, worker bindings/reply targets and closed-finding decisions when applicable | Relevant requirements, exact clean source, reproduction artifacts and limitations; scoped reads and focused execution; final replies in both modes and independent relevant-change checks |
| [Discussion](../schemas/discussion-input.schema.json) | Target finding IDs, new comment IDs, baseline finding history and prior assessments | Same reviewed snapshot; full investigation capabilities. Technical proposals require a separate verifier; code supplies validated dismissal commands, which bypass technical reassessment |

Diff/change inventories and reproductions use `artifact_manifest`; their IDs are stable, their bytes/digests retrievable, and their path/format described in the adapter result. The initial source checkout and comparison information must be available even when dependency setup fails. A source artifact is not replaced with a newer branch tip during investigation.

When technical assessment or a technical reply is required, review and discussion both end with the independent verifier producing assessments and final replies; code derives lifecycle actions. An empty review candidate pool with no required technical replies skips verification; a command-only discussion skips both technical agents. Review mode uses reviewer evidence and authenticated rebuttals; discussion also includes provisional investigation output. History import has its own replaceable/additive role prompt and explicit model/timeout settings. Payload customization may replace or extend only customizable role instructions; mandatory policy remains. validated_dismissals contains code-validated commands in discussion inputs; the orchestrator applies them in both modes without model approval. A command-only invocation needs no discussion or verifier agent; code acknowledges the command and recalculates the result.

## Logical tool inventory

These names define adapter capabilities, not endpoint paths or a claim that the SDK already implements them. The local MCP adapter implements the GitHub, Jira, Deltahub and artifact capabilities below; native runtime tools implement workspace operations and public web access. A concrete tool may map multiple logical operations provided the same scope and result requirements are enforced. GitHub/Jira/Deltahub endpoint details will be specified during implementation.

| Tool ID | Inputs | Result and restrictions |
| --- | --- | --- |
| `workspace.read` | Workspace ID, repository-relative path, optional line range | File text or binary metadata from the allowed checkout/artifacts; reject paths escaping its boundary |
| `workspace.search` | Workspace ID, query, path filters | Matching paths/lines plus truncation information |
| `workspace.exec` | Workspace ID, command/arguments, working directory, requested timeout | Exit status, redacted stdout/stderr, elapsed time, artifact refs; enforce remaining budget and local/development access. No CI suite, formatter/linter reruns or publication |
| `artifact.read` | Declared artifact ID, optional range | Validated immutable bytes/text and content digest; access only authorized artifacts, never arbitrary credential-bearing URLs |
| `github.read_pr` | Allowed repository, PR number, optional page cursor | PR metadata, reviewed/current commit identities, description, changed files/diff, review summaries, comments; distinguish snapshot data from a live observation |
| `github.read_thread` | Allowed repository, PR/thread or comment ID, cursor | Typed comments, authenticated actors, parent IDs, resolved/outdated state and review linkage |
| `github.read_file` | Allowed repository, explicit commit/ref, path | Source bytes with resolved SHA; contextual reads from other commits cannot replace the reviewed target |
| `github.search` | Allowed repositories, query, cursor | Related PR/code metadata and source links within the repository allowlist |
| `jira.read_ticket` | Allowed ticket key, cursor | Ticket fields/description, typed comments, attachment metadata and observation time |
| `jira.search` | Allowed projects, query, cursor | Related ticket summaries and retrieval references |
| `jira.read_attachment` | Allowed ticket/attachment ID | Bounded content or an explicit unsupported/too-large/unavailable result; validate retrieval origin/redirects |
| `deltahub.read_project` | Allowed project ID | Sanitized project review rules and context; no credentials or unrelated organization data |
| `deltahub.read_review` | Allowed project and review/finding ID, optional revision | Stored review/finding history, job result and evidence references needed for investigation; no callback writes or token renewal |
| `web.search` | Public technical query | Search results with URLs/timestamps within configured search mode; no private text or code in queries |
| `web.read` | Public result URL | Page content and provenance with bounded retrieval; no forwarding private-system credentials |

Read adapters return source identity, observation time, pagination/completeness status, and explicit errors. The worker saves material evidence plus its digest in private artifacts. An inaccessible page is not an empty result. Pagination must be exhausted where completeness matters, particularly prior reviews and replies. Size limits and allowed content types are configured and disclosed when they constrain investigation.

The worker supplies only the tool IDs appropriate to that stage, and the adapter checks `read_scope.repositories`, `jira_projects`, `deltahub_projects`, and web mode on every request. Agents cannot expand scope themselves. Fetched project settings are contextual observations: they do not silently replace the immutable request's review rules or prompts. Record any material change and handle it as changed input when appropriate.

GitHub writes, Deltahub progress/final-result submission, subscription credential renewal, and Secret Manager access are application operations, not agent tools. The trusted worker fetches the GitHub App private key from Secret Manager and generates scoped temporary tokens; agents never receive that key or publisher credentials. Deltahub retains Codex OAuth renewal ownership.

## Selected transport and authentication

The worker ships a small Python MCP adapter and launches a separate stdio adapter process for each agent session that needs it. The adapter and all agent sessions run within the same Cloud Run task/instance. There is no public MCP server or browser login. The worker pins its command, tool allowlist and read scope; repository files cannot supply or replace the server. Agent → MCP calls travel over local process pipes, so that hop has no password, cookie, OAuth login or bearer token. Process startup and restricted access to the pipes establish which session may call it. Stdio itself is not a security boundary against repository execution; the runtime restrictions still apply.

The agent supplies operation arguments, never authentication material. Trusted adapter/credential code attaches credentials to outbound API calls and returns sanitized results. The chosen native Codex workspace/web capabilities must be exercised against the pinned runtime; missing capabilities produce a declared limitation/failure, not an undisclosed replacement with unrestricted shell HTTP commands. See [runtime authentication](runtime-and-recovery.md#jira-service-account-authentication) for the Jira flow and existing GitHub App flow.

GitHub reads use short-lived, read-scoped App installation bearer tokens minted by the trusted worker from the Secret Manager private-key reference. Publishing and authenticated clone/fetch remain application operations with their separately scoped tokens. Jira uses service-account OAuth client credentials and a temporary bearer token. Deltahub adapter operations reuse the trusted worker's backend authentication integration; the precise Deltahub endpoints and authentication contract remain an implementation integration item, not an agent login. Artifact reads use the worker's scoped GCP service identity. Never expose these credentials through tool arguments/results, prompts, logs or repository subprocesses.

## Frozen requirements and reply routing

All projections retain the same authoritative requirements from the immutable request. Integration adapters distinguish frozen content, supporting live evidence, and authoritative-context change notices. Live Jira edits cannot silently replace the normative input of an unfinished stage or invalidate the meaning of reused work; the worker records and reports them for a new request while continuing against the snapshot.

Discussion inputs receive worker-owned reply_targets, keyed by reply_target_id with fixed finding/source mappings. In both modes, verifier final_reply_targets use the same identities. One finding may have several conversations. Verifier inputs also include current canonical candidate source membership so code can validate bindings independently of agent-generated text.
