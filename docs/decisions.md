# Decisions, limitations, and source notes

This is the current decision register, with accepted limitations and the evidence still required during implementation. The detailed workflow and contracts define the behavior.

## Agreed decisions

| Area | Decision |
| --- | --- |
| Scope | Cloud Run worker image and integration contracts; eligibility/scheduling/export enforcement belong to Deltahub |
| Account | Owner's Business subscription for POC; credentials already stored in Secret Manager; no API-billing fallback |
| Input | Immutable GCS object, exact generation, job ID; credential references rather than secret values |
| Runtime | Python orchestrator with Codex Python SDK and pinned runtime |
| Repository setup | Explicit project recipe; continue source inspection if setup fails |
| Agent placement | All agents inside one Cloud Run task/instance, separate worktrees/environments |
| Resources | Local or explicitly designated development only; never staging or production |
| Docker | Arbitrary nested Docker excluded; sidecar profiles or alternate execution backend are future options |
| Triage | Bounded model/effort allowlist; mandatory lenses and explicit quality ownership enforced in code |
| Default limits | Four reviewers, two concurrent agents, two additional stage attempts, 30-minute cumulative quota wait, two-hour execution deadline |
| Quality rules | Scope/completeness, English, internal references are major; custom rules blocking; fixtures exempt from language |
| CI | No CI-suite/formatter/linter reruns; focused reproductions allowed |
| Stacked PRs | PR2-only changes; PR1 context, no PR1-only findings on PR2 |
| Unrelated issues | May be reported separately, never block this PR |
| Deduplication | Before verification, when the combined new/history pool has at least two candidates, regardless of reviewer count; preserve originals |
| Verification | One verifier initially, bounded batches if necessary; valid/invalid/unverifiable plus evidence |
| Unverifiable | Published and blocking when major/blocking, open, and PR-related |
| Reviewer failure | Retry failed stage; fail execution without verdict if required stage cannot finish; preserve completed outputs |
| Historical human findings | Reassess and link; explain invalidity in overview; do not auto-rebut/resolve human threads |
| Dismissal | Explicit non-author human dismissal is authoritative per finding; resolving a thread is insufficient |
| Discussion | Full investigation capability; revise existing report/verdict without approving newer code |
| Follow-up | New changes plus unresolved findings, full diff as reference; failed predecessor or unreliable baseline can lead to fresh review |
| Publication | Programmatically compose Check verdict plus comment-only PR review; verify suggestions separately |
| Advancing PR | Finish and publish original commit's actual result, including inline comments; newer revision is informational only |
| Anchor rejection | Overview fallback with original location, not silent relocation onto newer code |
| Recovery | Durable completed-stage artifacts; mid-conversation agent restoration is not required |
| Auth renewal | Deltahub renews shared Codex OAuth credentials; trusted worker code mints replacement GitHub installation and Jira service-account access tokens |
| External tools | Scoped read tools for agents; trusted application code publishes |
| Trust | Source content cannot change workflow/tool/credential policy; Jira requirements and explicit dismissals retain their defined authority |
| Reporting | Publish first, then save one report including publication results/failure; later delivery updates create immutable revisions; incremental checkpoints throughout |
| Prompt ownership | Versioned app-owned mandatory policy and default role prompts; role replacements/additions allowed, mandatory requirements cannot be replaced |
| Agent output schemas | Simple structural definitions with mechanically bundled refs; conditional/input-dependent checks in Python; no hand-maintained alternate schemas |
| Discussion verification | Independent verifier for technical reassessments; command-only human overrides bypass technical verification |
| Fixed-state claims | Require evidence of a historical fix in the exact reviewed snapshot; newer fixes require a follow-up code review |
| Request/job identity | Exact retry retains request/payload, creates new job/execution with original/predecessor links |
| Platform retries | Cloud Run `max_retries = 0`; worker retries stages, Deltahub retries jobs |
| Role deadlines | Configurable per-attempt work limits, paused for explicit quota waits; overall deadline continues |
| Cancel/stop | Cancel is pre-flight through enqueued; stop is after start, using Cloud Run execution cancellation and graceful signal handling |
| Worker loss | Deltahub classifies terminal state using recorded stop intent; failures may receive linked retries, intentional stops do not retry automatically; retry worker reconciles progress; backend may close an abandoned running Check only |
| Dismissal syntax | Configured mention plus `/dismiss` and finding ID; optional reason; deterministic parsing and non-author human validation |
| GitHub key custody | Worker reads App key reference from Secret Manager and generates scoped ephemeral tokens; key/write credentials isolated from agent/repo execution |
| Final assessments and replies | In both modes the independent verifier produces assessments and final replies; code derives lifecycle actions. Review has no post-verifier reconciliation agent |
| Human import | Dedicated history_import prompt, customization, model and timeout; code stamps authenticated provenance and preserves original threads |
| Import coverage | Explicit accounting includes zero-finding units; sourced omissions use bounded correction and owner acknowledgment before completion |
| Closed findings | Quality owner decides retain/reassess; reopening requires independently verified relevant changes, not a file match or repeated objection |
| Discussion targets | Worker resolves triggering comments, commands, thread associations and optional finding IDs; no guessing |
| Read integration | App-owned local stdio MCP adapter per session inside the same task; native workspace/web tools |
| Jira credentials | Service-account OAuth client credentials; client ID/secret in Secret Manager, temporary access tokens renewed in memory |
| Requirement snapshot | Keep supplied requirements fixed; observed authoritative changes are recorded and reported to Deltahub for a new review request |
| Identity and replies | Globally unique finding IDs, source-derived assessment bindings and a separate target ID for each conversation |
| Revision ownership | Conditional reservation before publication; authorized terminal cleanup can release an abandoned reservation without resuming stopped computation |
| Assessment baseline | Track latest saved revision separately from latest completed assessment so failed/stopped revisions do not erase the baseline |
| Completion evidence | Require all planned computation and durable completion artifacts; compatible reused stages retain producer identity |
| Storage failure | Completed computation can report delivery failure with a durable checkpoint when report storage fails; no invented report reference |
| Source provenance | Typed source IDs resolve through metadata-only sources or documents; duplicate text is optional and must agree when present |

## Subscription-authentication applicability set aside

Subscription-authentication applicability is outside this specification’s scope. The POC continues to require Codex subscription authentication with Deltahub-owned OAuth renewal; no API-billing fallback is introduced. Validate practical token handling, renewal, quota telemetry and runtime capabilities against the pinned implementation when building the worker.

## Required feasibility checks

These are implementation verification tasks, not additional product decisions or completed experiments:

| Check | Evidence required |
| --- | --- |
| Subscription integration | Successful headless subscription-funded request; practical renewal and revoked-token behavior (applicability review excluded here) |
| Python SDK/runtime | Pinned compatible builds; structured output, concurrent sessions, model/effort selection, error/completion events, and tool configuration |
| Quota handling | Actual account's rate-limit/reset fields and errors; bounded pause/retry; missing telemetry behavior |
| Cloud Run sandbox | File/process/network permissions enforce selected boundaries without privileged Docker; publisher and account secrets inaccessible to repo commands |
| Repository setup | Representative Scrapy/Django/FastAPI dependency installs, native packages, and separate environments |
| Older GitHub review | Comment-only review on older head, changed lines, base changes, force-push, and rejected-anchor fallback |
| Delivery recovery | Ambiguous API acknowledgments, duplicate callbacks, publication reconciliation, and revision conflicts |

## Known limitations and accepted tradeoffs

- One instance shares CPU, memory, networking, and potentially development services. Worktrees are not a security or database isolation boundary.
- Optional execution may be unavailable; source-only review is allowed and must disclose limitations. Unverifiable major/blocking findings may require human discussion.
- A two-hour deadline and subscription quota may stop a review. Only completed durable work is reusable; unfinished in-memory reasoning may be lost.
- Subscription use competes with other use of the same account; per-instance concurrency does not impose an account-wide limit across jobs.
- GitHub cannot provide an atomic 'check current head, then publish' transaction. Exact commit attribution and Deltahub identity checks provide correctness.
- A Check's commit identity alone does not represent a changed base or different PR using the same head.
- GitHub may reject an older inline anchor; publication fallback preserves the finding. Force-pushed objects or lost repository access can also affect source links/delivery.
- A generic Python slim image cannot execute every repository without configured runtimes/native libraries. Arbitrary Docker/Compose support is outside the initial environment.
- Reports can identify what was inspected and verified; they do not prove exhaustive defect detection or guarantee zero false positives.

Retention periods, precise model IDs/efforts, runtime pins, image resource sizing, attachment limits, and endpoint paths are deployment/implementation configuration. The provided schemas expose the necessary contracts without inventing fixed values for these choices. If implementation requires a material change to agreed behavior, surface it explicitly instead of silently narrowing the POC.

## Primary sources consulted

Sources were read during design; implementation must verify the chosen pinned versions and current platform behavior.

- [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk): Python and TypeScript integrations; Python SDK controls a local app-server and includes a pinned runtime dependency.
- [Codex authentication](https://learn.chatgpt.com/docs/auth): subscription versus API-key authentication.
- [Codex app-server](https://learn.chatgpt.com/docs/app-server): account/authentication interfaces, external token renewal, and rate-limit telemetry; hosted-service applicability note.
- [Sign in with ChatGPT plan usage](https://developers.openai.com/siwc/token-sharing-open-source): integration scope and remotely hosted application process.
- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) and [web search](https://learn.chatgpt.com/docs/web-search): tool integration and search configuration; search controls do not replace command-network controls.
- [Cloud Run execution overrides](https://docs.cloud.google.com/run/docs/execute/jobs): per-execution args/environment/task/timeout overrides.
- [Cloud Run secrets](https://docs.cloud.google.com/run/docs/configuring/jobs/secrets): Secret Manager integration.
- [Cloud Run retries/checkpoints](https://docs.cloud.google.com/run/docs/jobs-retries): restart-safe outputs and persistent checkpoints.
- [Cloud Run task timeout](https://docs.cloud.google.com/run/docs/configuring/task-timeout): timeout applies to task attempts; application budgeting must account for retries.
- [Cloud Run container contract](https://docs.cloud.google.com/run/docs/container-contract): runtime constraints and no privileged containers.
- [Cloud Run multi-container jobs](https://docs.cloud.google.com/run/docs/create-jobs): sidecar support and readiness configuration.
- [GitHub Checks](https://docs.github.com/en/rest/checks/runs), [reviews](https://docs.github.com/en/rest/pulls/reviews), and [review comments](https://docs.github.com/en/rest/pulls/comments): commit attribution, publication, and possible validation errors.

## Deliberate exclusions

- Do not cancel a completed review or skip findings merely because newer commits exist.
- Do not introduce an 'incomplete' code-review verdict to represent failed execution.
- Do not run a separate Cloud Run instance for each agent in the POC.
- Do not rerun CI suites just because review agents can execute code.
- Do not interpret a resolved GitHub thread as an explicit dismissal.
