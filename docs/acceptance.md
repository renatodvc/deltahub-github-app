# POC acceptance scenarios

These are implementation acceptance criteria, not claims that a worker has already been built or tested. Schema/example validation is a separate documentation check.

## Review behavior

| ID | Scenario | Expected result |
| --- | --- | --- |
| R01 | Small first review with no findings or historical issues | One reviewer may cover technical work and the complete quality checklist; valid empty output; no deduplication/verifier needed; approved |
| R02 | Mandatory security lens on a small PR | Triage includes it regardless of diff size; orchestrator rejects a plan omitting it |
| R03 | Tests/fixtures dominate the diff | Effective size excludes configured paths; raw statistics remain visible; excluded files remain available to review |
| R04 | Multiple reviewers find the same issue | One canonical candidate; all raw findings and sources retained; deduplication statistics correct |
| R05 | Multiple different issues affect one line | Distinct canonical findings; location alone does not cause deduplication |
| R06 | Verifier establishes a major PR defect | Requires changes; inline comment or overview fallback contains evidence |
| R07 | Verifier refutes all candidates | Approved; invalid findings remain in JSON and are not published as active defects |
| R08 | Verifier cannot settle a major PR defect | Unverifiable finding is published with missing evidence and how to settle it; requires changes |
| R09 | Only minor valid/unverifiable findings | Approved with advisory findings |
| R10 | Pre-existing defect outside the PR | Separate unrelated section; does not block even if severity is blocking |
| R11 | PR2 targets PR1 | Review PR2-only changes; use PR1 as context; do not report PR1-only issues on PR2 |
| R12 | Ticket scope, English, or internal-reference violation | Major severity; fixtures exempt only from the language rule |
| R13 | Custom project rule violated | Blocking severity; supplied rule ID and evidence retained |
| R14 | Jira and PR description disagree | Jira takes precedence; recent explicit Jira clarifications carry weight |
| R15 | Jira instructions genuinely conflict | Concrete requirement ambiguity can be a finding; no invented certainty |
| R16 | CI has already passed | Do not rerun CI/formatters/linters; a focused reproduction is allowed |
| R17 | Suggested patch does not actually fix a valid defect | Retain finding; omit unverified/rejected suggestion block |

## Follow-up and discussion

| ID | Scenario | Expected result |
| --- | --- | --- |
| F01 | New commits after a completed review | Focus on new changes and unresolved findings; full current PR diff remains reference |
| F02 | Previous review failed | New changed input can start as a first review; no failed review treated as a completed baseline |
| F03 | Force-push/retarget makes old comparison unreliable | Fresh review with recorded fallback reason |
| F04 | Follow-up finds a defect missed earlier in unchanged PR code | May block according to severity; do not misclassify it as unrelated |
| F05 | No new discoveries but unresolved prior findings exist | Account for and assess prior findings before verdict; do not take the zero-new-findings shortcut |
| F06 | Author disagrees with an AI finding | Investigate; acknowledge and invalidate if convinced, otherwise reply with evidence and retain it |
| F07 | Non-author argues against a finding without dismissing it | Evaluate the argument; do not treat disagreement as an override |
| F08 | Non-author issues a valid `@handle /dismiss finding-id` command for one of two findings | Only that finding is dismissed; actor/comment/history recorded; the other remains open |
| F09 | Author tries to unilaterally dismiss a finding | Treat as disagreement requiring reassessment, not authoritative override |
| F10 | Thread was marked resolved with no explanation | Neither dismissal nor proof of a fix |
| F11 | Human finding remains valid | Include/link existing thread and gate by severity; no duplicate inline comment |
| F12 | Human finding is invalid or fixed | Explain invalid assessment in overview or record fix evidence; do not automatically rebut/resolve human thread |
| F13 | Discussion settles all blocking findings without a new commit | New report revision and updated Check/overview approve the same reviewed head/base |
| F14 | Discussion cites a fix on a newer commit | It cannot approve newer code; the new review verifies that version |
| F15 | Dismissed issue is unchanged | Dismissal persists; an unrelated commit does not reactivate it |
| F16 | Relevant code/requirements change after dismissal | Reassessment can reactivate with explicit evidence/rationale |
| F17 | Two discussion jobs overlap | Revision/serialization control prevents older result overwriting newer state |

## Runtime and recovery

| ID | Scenario | Expected result |
| --- | --- | --- |
| E01 | Immutable input object has a newer generation | Read the requested generation only; never silently switch |
| E02 | Requested Git revision is unavailable | Fail explicitly; do not checkout latest as a substitute |
| E03 | Setup fails but code is readable | Continue inspection; disclose limitation; use unverifiable only for specific unsettled assertions |
| E04 | Reviewer modifies files to reproduce a defect | Other reviewer and verifier workspaces remain clean and independent |
| E05 | Mutable development resource cannot be isolated | Serialize investigative access; no staging/production use |
| E06 | One reviewer fails transiently | Retry it within allowance; retain other completed outputs |
| E07 | One reviewer exhausts attempts while others finish | No deduplication/verifier/publication of findings; execution failure and null verdict; durable successes reusable |
| E08 | Agent returns malformed output repeatedly | Bounded repair/retries; fail stage; never interpret absent output as no findings |
| E09 | Verifier dies before assessing candidates | Stage failure; pending candidates are not converted to unverifiable findings |
| E10 | Quota reset is within remaining wait and total deadline | Save progress, coordinate waiting, recheck limits, continue if available |
| E11 | Reset is beyond allowance | Terminate promptly with retry-later reason and retained outputs |
| E12 | Multiple quota waits occur | Cumulative allowance applies once per execution, not per agent/event |
| E13 | Reset metadata is unavailable | Bounded backoff, then failure; do not assume immediate availability |
| E14 | Codex OAuth token expires | Obtain renewed credentials through Deltahub; no independent refresh races among agents |
| E15 | Container is abruptly killed | Only durable work is reusable; absence of final callback does not imply approval |
| E16 | Execution fails after quota exhaustion | Cloud Run performs zero task retries; Deltahub creates a linked later job retaining the immutable request, and the new worker reuses compatible checkpoints |
| E17 | Exact retry after saved reviewer outputs | Reuse compatible artifacts, restart only unfinished stages; no dependency on in-memory conversation state |
| E18 | Project requires unsupported Docker environment | Record execution limitation; inspect source; future runtime options documented |
| E19 | Attachment is unsupported or too large | Record omission; no claim it was read; preserve applicable finding uncertainty |
| E20 | Repo/Jira/web text instructs bypassing verification | Treat as evidence content; fixed workflow remains enforced |
| E21 | Repository config requests additional tools/secrets | It cannot alter the explicitly configured agent environment |
| E22 | Sandbox/network restrictions do not work on Cloud Run | Feasibility check fails; do not claim development-only/read-only enforcement based on prompts alone |

## Publication and contracts

| ID | Scenario | Expected result |
| --- | --- | --- |
| P01 | Y is pushed while X is reviewed | Publish X's actual verdict and findings against X; never cancel solely because Y exists |
| P02 | Base changes while head stays X | Historical result retains original base identity; cannot satisfy the new Deltahub requirement |
| P03 | GitHub accepts older inline anchors | Publish with explicit reviewed commit; outdated UI state is acceptable |
| P04 | GitHub rejects a specific anchor | Preserve finding in overview with original location; never silently map onto newer code |
| P05 | GitHub returns rate limit/permission error | Treat as delivery error, not an anchor fallback or invalid finding |
| P06 | Publication succeeds but response is lost | Reconcile known markers/IDs before retry; no duplicate review/comments |
| P07 | Computation succeeds but publication fails | Keep computed verdict/report; retry delivery without rerunning agents |
| P08 | Deltahub callback fails | Durable final report/outbox retained; retry/reconcile; gate must not infer success from silence |
| P09 | Old attempt or duplicate callback arrives late | Deduplicate and enforce attempt/revision ordering; no state regression |
| P10 | Same SHA is used by different PR/base snapshots | Separate review identities and Check IDs; no cross-application of results |
| P11 | Credentials appear in command output | Redact before persistence/publication; do not expose `.env` contents |
| P12 | Unknown token usage | Report null/absent, not zero or invented monetary spend |

## Integration and contract invariants

These scenarios exercise integration boundaries and contract invariants beyond the core review flow.

| ID | Scenario | Expected result |
| --- | --- | --- |
| S01 | Agent needs related Deltahub project/review context | Scoped read adapter returns sanitized typed data; no credential or callback tool is exposed |
| S02 | Build each stage input | Includes relevant immutable source/context and correct prompt/assignment; excludes worker credentials and publication configuration |
| S03 | Follow-up review receives pushback and a per-finding human dismissal | Same lifecycle/reply contract as discussion; code-review actions agree with verifier evidence; only the explicitly dismissed finding is overridden |
| S04 | Prior reviews have replies, resolved threads, and dismissed GitHub reviews | Typed states/parent IDs/authors remain distinguishable; GitHub review dismissal or thread resolution does not implicitly dismiss every finding |
| S05 | All reviewers return empty discoveries while one major prior issue remains | Code seeds that issue from the ledger; verifier assesses it; it can still require changes |
| S06 | Agent echoes a different reviewer ID or commit hash | Agent-output schemas reject those fields; code derives identities/hashes from its stage inputs |
| S07 | Quality owner omits a built-in check or one custom rule | Schema rejects missing built-ins; semantic coverage check rejects missing/duplicate/unknown custom-rule IDs |
| S08 | Triage selects a required lens and adds its own scope instructions | Worker retains exact configured lens instructions/version and prompt reference; added instructions cannot replace mandatory coverage |
| S09 | Deduplicator rewrites a singleton, drops an input, or invents an ID | Singleton rewrite and invalid partition fail Python semantic validation; source records remain intact |
| S10 | One anchor in a create-review request is rejected | No partial success assumed within the rejected request; reconcile, correct/fallback, and retry the request. Separate successful operations retain their IDs |
| S11 | Evidence has several code locations | Only explicit primary location is considered for inline placement; diff validation rejects incompatible side/revision/range |
| S12 | Payload requests a runtime different from the launched image | Worker reports incompatible configuration; Deltahub must choose matching deployed Job before launch |
| S13 | Two reviewers and verifier need dependencies | Each executing workspace runs setup independently; clean verifier source and writable environments remain isolated |
| S14 | Computation is complete but delivery pending | `review_completed` references a durable computation checkpoint with null report; `finished` requires publication complete and the saved report/reference |
| S15 | Terminal computation failure occurs before report composition | `failed` carries stable code and retained artifact refs with null report; no approval inferred |
| S16 | A required stage fails, but retry allowance remains | `stage_failed` is nonterminal; no false terminal job state; attempts remain bounded |
| S17 | Left-side anchor uses base tip instead of actual diff merge base | Reject inline placement or use overview; do not publish on an incorrect revision |
| S18 | Instance dies while another agent is running, without a shutdown callback | Outputs from agents/batches already completed are durably checkpointed and reusable; recovery does not depend on a final report or signal handler |
| S19 | Stop cleanup cannot finish within the platform shutdown window | Previously persisted progress remains usable; no assumption that final uploads/callbacks succeeded; reconcile remote writes with ambiguous acknowledgments |
| S20 | Project replaces every customizable reviewer instruction | App mandatory policy remains in assembled prompt; built-in checks/custom-rule coverage and severity remain enforced by code |
| S21 | Output is structurally valid but has invalid conditional fields | Python validation rejects wrong severity, missing invalid reason, unverifiable without evidence gap, or changed singleton; bounded stage repair applies |
| S22 | Discussion proposes invalidating the last blocker | Independent verifier assesses it before state/verdict changes; final reply follows verification, not the provisional proposal |
| S23 | Author cites a fix only in a newer commit | Old snapshot is not marked fixed; new follow-up reviews changed code and remaining findings |
| S24 | Historical fix already exists in the discussion snapshot | Independent evidence can mark it fixed; a false original assertion is refuted instead |
| S25 | Publication succeeds before final report upload, then worker dies | Retry reconciles checkpointed revision/remote IDs and saves report without rerunning completed agents or duplicating writes |
| S26 | Failed publication report was saved; retry later succeeds | New linked job, same request/input, next immutable report revision with delivery-update reason and unchanged assessment |
| S27 | Exact retry gets a new Deltahub job ID | Request bytes/generation/digest remain unchanged; invocation carries new job/lineage; callbacks target that new job |
| S28 | Per-role attempt deadline expires | Stop that agent, record stage_timeout, retry within remaining attempts/global deadline; explicit quota pauses only role work time |
| S29 | Pre-flight cancel versus running stop | Cancel prevents launch; stop records intent and requests Cloud Run execution cancellation; no automatic retry of intentional stop |
| S30 | Worker disappears after a completed Check | Deltahub records operational failure without replacing completed Check; retry worker determines remaining work |
| S31 | Quoted command, author command, bot command, wrong finding ID or duplicate delivery | No unauthorized/ambiguous override; valid accepted command is applied once and persisted with actor/source |
| S32 | GitHub token expires during a long review | Trusted worker generates a fresh scoped token using its Secret Manager key; no token value in payload, persistent Git URL, prompt or checkpoint |

## History, identity, and delivery edge cases

| Case | Expected result |
| --- | --- |
| Human thread contains zero, one or multiple assertions | Import accounts for every source unit; code stamps authenticated human origin; extracted issues require independent verification |
| Import output omits a source unit or invents authorship | Reject the attempt; no verdict from incomplete required import |
| One reviewer rediscovers a historical issue without linking its ID | Both candidates enter deduplication; stable historical identity survives the merge |
| Several reviewers yield only one combined candidate | No deduplication agent; unchanged singleton proceeds to verification |
| Verifier discovers material evidence while writing a reply | Investigate within the same attempt and return consistent assessment/reply; uncertainty may be unverifiable, runtime failure follows bounded retries; no post-verifier loop |
| Historical c1 and current c1 identify different candidates | Resolve through explicit current bindings, never historical candidate-ID coincidence |
| Exact-input discussion retry after its own failed/stopped revision | Original input remains unchanged; reservation advances past only same-request lineage revisions; an intervening different request causes conflict |
| Saved failed/stopped report followed by successful retry | Next immutable revision, execution_retry reason, predecessor precondition and new job owner |
| Crash before/after report save or reservation pointer update | Conditional takeover reconciles remote writes/report; no overwrite, blind increment or live-owner takeover |
| Complete computation with GitHub delivery failure | Computation verdict preserved; typed delivery_failure and delivery_failed event |
| Fresh review after rewritten history | Preserve known finding IDs, dismissals and threads independently of diff-baseline fallback; genuinely new issues get globally unique IDs; an old command cannot target an unrelated issue |
| Worker dies after Check registration | Deltahub has Check ID and owner; cleanup cannot overwrite a newer owner's result |
| Published inline comment | Finding thread_links and publication records agree; agent reply body cannot select an arbitrary URL |
| Typed entity with metadata-only source | URI/observation resolve without a duplicate document; missing/duplicate source resolution rejected |

## Discussion and closed-finding safeguards

| Scenario | Expected result |
| --- | --- |
| Discussion investigator accepts rebuttal but verifier rejects it | Two technical agents; verifier's assessment and final reply retain the issue. No third reconciliation invocation |
| Verifier output omits or duplicates a required final reply | Invalid stage output; no technical lifecycle update or publication |
| Deltahub omits finding IDs, or sends an empty list, with a valid dismissal command | Worker resolves the command's exact target; deterministic authorized override, no duplicate backend parser |
| General comment has neither an explicit target nor a known finding thread | Actionable invalid_input; no guessed reassessment/dismissal or new verdict |
| Command targets one finding while optional IDs include others | Command never dismisses additional findings |
| Quality owner omits a closed finding or proposes reassessment without change evidence | Invalid required stage output; not silently retained/reopened |
| Unrelated edit touches a fixed finding's file | Explicit retain_closure decision; no automatic reopening |
| Caller/dependency/configuration or Jira requirement changes undermine closure | Reassess with concrete evidence even if the original file is unchanged |
| Verifier confirms old defect but finds no relevant change since dismissal | Dismissal persists; new disagreement alone cannot overturn the human override |
| Verifier confirms relevant change and valid/unverifiable issue | Code may reactivate, preserving closure history and renewed evidence |
| Local MCP integration read | Separate restricted stdio adapter per session, same Cloud Run task; no public server or agent-supplied credentials |
| Jira access token expires during investigation | Trusted client-credentials renewal and bounded retry; no interactive login or temporary-token Secret Manager writes |

## Recovery and completion invariants

| Scenario | Expected result |
| --- | --- |
| Stopped discussion leaves an active reservation and will not be retried | Authorized cleanup confirms terminal state, reconciles writes and saves/reconciles the predecessor terminal report; clears reservation without running agents or finishing stopped publication |
| Old owner or cleanup owner is still running | No takeover from elapsed time alone; preserve ownership and reject conflicting writes |
| Cleanup advances report revision | Preserve latest completed assessment pointer; stale new request is refreshed by Deltahub rather than rerunning abandoned computation |
| Verifier retains a human dismissal and answers a new comment | Serializable retain_closure action, unchanged lifecycle, final replies retained |
| Two conversations concern the same finding | Distinct reply_target_ids, complete independently routed replies, one lifecycle assessment |
| Final report upload fails after durable computation | delivery_failed with artifact_io_failed, null report/reference and computation checkpoint; no fabricated URI or recomputation |
| Two known finding/candidate bindings are swapped | Reject because source membership does not match, even when both ID sets are complete |
| Completed report includes a failed or missing required reviewer | Reject; no completed verdict from unsuccessful required work |
| Retry reuses a completed stage | Succeeded stage plus verified producer completion artifact and compatible inputs; missing/fabricated reuse fails |
| Live Jira edit adds a requirement after payload creation | Continue using frozen requirements; durable context-change event/report notice requests a new Deltahub review |
| Unfinished stage or retry sees newer Jira text | New text cannot silently become its authoritative requirements while other stages retain old results |

## Verification and prompt isolation

| Scenario | Required result |
| --- | --- |
| Follow-up review includes an author rebuttal | Independent verifier returns assessment and final reply; code derives action without a reconciliation agent |
| Review has multiple conversations for one finding | Exactly one reply per target; one consistent assessment, authenticated destinations |
| Closed finding requires a reply while closure is retained | Include it in verification; closure check and final reply preserve closure absent confirmed relevant changes |
| Discussion role prompt/model/timeout changes | History-import instructions and explicit settings remain unchanged |
| Project replaces history_import prompt | Import-only replacement plus mandatory policy; complete source-unit accounting and authenticated provenance remain required |
| Payload or stage still requests removed reconciliation workflow | Reject obsolete configuration/stage/failure code rather than accepting a hidden extra loop |

## Human import omission repair

| Scenario | Required result |
| --- | --- |
| Quality owner receives import results | Explicit complete accounting, including units with zero assertions and their reasons |
| Owner spots an asserted human defect classified as empty | Sourced import_omissions entry; no duplicate AI finding or successful owner stage yet |
| Correction imports the missed assertion | Code stamps human provenance, binds stable ID and original thread; independent verifier later assesses validity |
| Importer rejects a suspected omission as praise | Source-specific resolution; updated accounting returns to owner for acknowledgment, no silently discarded concern |
| Correction omits a requested resolution or deletes an existing assertion | Invalid output; preserve prior accounting and bounded attempt policy |
| Owner acknowledges an old accounting revision | Reject completion; no pooling/verification from stale coverage |
| Correction remains unresolved after allowed passes | stage_attempts_exhausted, preserved work, no verdict; exact retry does not reset pass budget |
| Worker dies while accepting a correction | Resume checkpointed pass, reconcile accounting/ledger/ID allocations; no duplicate human finding |
| Accepted correction reaches publication | Original human thread is linked, no new AI inline thread; report retains final accounting and immutable correction history |

## Implementation sequence

1. Validate the pinned SDK/runtime/sandbox combination and practical subscription credential handling in a disposable Cloud Run environment.
2. Implement schemas, immutable input loading, fixed checkout, setup, scoped read tools, and one reviewer with quality control.
3. Add triage fan-out, deduplication, verification, deterministic verdicts, and stage checkpoints.
4. Implement Check/comment publication, older-commit anchors/fallbacks, idempotent delivery, and Deltahub callbacks.
5. Add historical findings, incremental follow-up, discussion revisions, and human dismissals.
6. Exercise recovery, quota waiting, workspace/resource isolation, and the full acceptance matrix.

This sequence paces delivery; it does not remove any agreed POC feature.
