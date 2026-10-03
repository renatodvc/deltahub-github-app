# Runtime, isolation, and recovery

## Container and startup

Use a Python slim base with at least `git`, `curl`, CA certificates, the Python orchestrator, and the pinned Codex Python SDK/runtime. Build for a Cloud Run-supported architecture. The worker's Python dependencies are isolated from repository dependencies so project installation cannot replace the orchestrator or SDK packages.

One Cloud Run execution contains one task/instance for one review/discussion request. Within it, Python manages concurrent Codex sessions. The default maximum of two includes any overlapping agent sessions; stage barriers normally prevent overlap between reviewers and later stages.

Startup validates bootstrap values, downloads the exact payload generation, computes its digest, validates the schema and permissions, establishes the execution deadline, loads compatible checkpoints, obtains credentials, fetches exact Git history, and creates/reconciles the GitHub Check. Do not evaluate arbitrary shell substitutions from repository names, branch names, payload strings, or filenames. Treat them as data and use argument arrays wherever possible.

## Checkout and environment setup

Fetch and check out the supplied head in detached form; fetch enough base/history to calculate the PR diff correctly. Branch names alone are not a review identity. Do not pull changes into a running checkout. If a force-push makes the required object inaccessible, fail with `revision_unavailable`; do not substitute another commit.

Use a clean source checkout and separate worktrees for reviewers. Each has its own writable dependency environment, temporary files, and investigative artifacts. The verifier starts from clean reviewed source, not a reviewer's mutated tree. Pass useful reproductions explicitly as artifacts. Editable dependency installations must point at the correct agent workspace.

Run dependency installation, preparation commands, and development `.env` materialization once per writable agent workspace/environment before its first use. This includes a fresh verifier workspace and any discussion workspace that executes code; an agent stage without execution needs no installed workspace. Reuse a successfully prepared workspace only for that same agent attempt when safe. A restarted unfinished stage gets a clean workspace and setup again. Read-only downloads/wheel caches may be shared; writable environments, editable installs, `.env` files, and setup-created state must not be shared between agents. Record setup status per workspace, so one failed setup does not falsely mark another environment ready.

Execute the configured setup recipe, including dependency installation and development `.env` materialization. Record commands, exit status, and redacted diagnostics. Setup failure permits source-only review when source is readable. Agents may install additional local investigative dependencies within their own environment. They must not repair the repository by pushing changes or silently claim runtime verification when setup did not succeed.

Python version and native library requirements vary. Before launching, Deltahub maps the requested `runtime_profile` and `python_version` to a deployed Cloud Run Job whose image contains the required interpreter/native packages. The worker cannot select its own already-running image. Its startup checks compare the payload with image runtime metadata and the actual interpreter; an incompatible profile is `unsupported_configuration`, rather than silently executing with a different Python version. Record the selected image digest and actual interpreter version in runtime provenance. Project dependency failures after compatible startup still permit source-only review. A framework-agnostic reviewer is not a promise that one universal image can execute every repository.

## Isolation and tool permissions

Worktrees isolate normal file edits, not processes, credentials, network access, or databases. All agents share the instance's CPU and memory. Separate ports and development-resource namespaces where needed; serialize investigations against a mutable shared resource when isolation is unavailable.

The orchestrator owns GitHub write credentials and publication operations. Agents get the scoped GitHub, Jira, Deltahub, web, and workspace tools in [agent-inputs-and-tools.md](agent-inputs-and-tools.md). Use an explicitly configured MCP server/tool adapter; do not assume the SDK bundles ready-made Jira or Deltahub integrations. Disable automatic loading of repository-provided hooks, MCP servers, or agent configuration that could change these boundaries.

Only local and explicitly designated development resources are allowed. Do not inject staging/production credentials. Project configuration must identify allowed resources; hostname guessing and a prompt saying 'development only' are insufficient enforcement. Raw shell commands can bypass read-only MCP tools if given broader credentials or network access. Validate the actual sandbox, filesystem, subprocess environment, metadata-server access, and network restrictions in the selected Cloud Run runtime before claiming these boundaries are enforced. If those restrictions cannot be implemented within the chosen runtime, record the limitation and resolve it before enabling unrestricted investigative execution.

Repository install scripts and code are executable inputs. Limit their permissions and keep publication/account credentials out of their accessible environment. Secret redaction is defense in depth, not a substitute for access separation.

## Docker and service dependencies

The POC does not promise arbitrary Docker-in-Docker or Compose execution. Cloud Run does not provide privileged containers. Local processes and explicitly permitted development services are supported where configured.

Future options preserve the worker/report contracts:

- Known service dependencies: job variants with PostgreSQL/Redis sidecars, explicit readiness/shutdown behavior, and isolated per-agent data.
- Arbitrary Compose environments: a Docker-capable execution backend, with the same fixed review input and evidence contracts.

Do not mistake sidecars for unrestricted nested Docker support.

## Subscription and authentication

Use the owner's Business subscription for the POC. Deltahub stores OAuth credentials in Secret Manager and owns token renewal. Reference credentials in the payload; load material only through trusted credential handling. Subscription-authentication applicability is outside this specification’s scope; the subscription requirement and token-renewal ownership remain unchanged.

Token expiration and subscription exhaustion are distinct:

- On an authentication-expiration error, request fresh credentials through Deltahub. Do not let parallel agents race to rotate shared refresh credentials. Revocation or required interactive reauthentication terminates with an actionable auth failure.
- On a subscription limit, stop redundant requests from affected agents, preserve completed outputs, and assess the reported reset time. An account-wide limit does not justify hammering it through another agent.
- If all blocking quota windows have usable reset information within the remaining waiting allowance and execution deadline, wait and recheck. A reset estimate does not guarantee the next request succeeds.
- If the reset is farther away than the allowance, terminate promptly as retryable later. If no reset time is available, use bounded backoff within the allowance.
- Count cumulative wall-clock quota waiting once for the execution, not once per sleeping agent. The default allowance is 1,800 seconds. Persist consumption for audit and recovery within this execution. A deliberately scheduled retry is a new linked Deltahub job and execution with a new execution allowance.

Do not conflate a network/service error with quota exhaustion. Retry transient errors within bounded policies. No API-key fallback or silent account/model substitution. Retry scheduling after exhaustion belongs to Deltahub.

## GitHub App credentials and clone authentication

Store the GitHub App private key in GCP Secret Manager. The immutable request carries `github_app_id`, `github_installation_id`, and `github_private_key_secret_ref`; it never carries the private key or an installation token. Trusted application code reads the authorized secret, signs the App JWT and requests installation tokens from GitHub. Tokens expire after one hour; cache them in protected memory and generate replacements before expiry as needed, using returned expiry metadata. Do not create a Secret Manager version for each temporary token. Key rotation alone does not change reviewed code or invalidate completed investigation.

Scope tokens to explicitly allowed repositories and permissions. Clone/fetch and read adapters use read-only installation credentials; the publisher uses the permissions required for Checks and PR reviews/comments. HTTPS Git access uses the Contents permission. Supply credentials through a controlled credential helper/askpass mechanism and prevent them from appearing in logged argv, persisted remote URLs or Git config. Obtain fresh credentials for later authenticated fetches; never substitute a new commit when authentication fails.

The private key, token-minting authority and publisher tokens are accessible only to the trusted orchestrator/credential handling, not to agents, repository commands, install scripts, prompts, checkpoints or reports. Read adapters use their own bounded authority. Worktrees do not enforce this separation; the runtime sandbox must restrict secret files, process inspection, inherited environment, metadata-service identity and network capabilities. A restricted token does not restrict an exposed App private key, so do not claim token scoping alone protects key custody. Deltahub still owns Codex OAuth renewal; it is not the GitHub token broker in this POC.

## Jira service-account authentication

The selected Jira Cloud authentication is service-account OAuth 2.0 client credentials. `credentials.jira_auth` is `oauth_client_credentials`; `jira_cloud_id` identifies the authorized Jira site, and `jira_credential_ref` references a Secret Manager JSON value containing `client_id` and `client_secret`. The trusted worker reads that reference using its GCP service identity. Validate the cloud ID and requested project scope against deployment authorization, not merely model-supplied arguments.

Credential handling posts form-encoded `client_id`, `client_secret` and `grant_type=client_credentials` to `https://auth.atlassian.com/oauth/token`. Use the returned access token as `Authorization: Bearer` for Jira API calls through `https://api.atlassian.com/ex/jira/<cloudId>/...`. Atlassian documents a 60-minute token lifetime and requires centralized user management for this service-account capability. Provision the account with the required read scopes and project permissions. These are deployment prerequisites. See [Atlassian's service-account OAuth documentation](https://support.atlassian.com/user-management/docs/create-oauth-2-0-credential-for-service-accounts/).

Cache temporary tokens only in trusted runtime memory, respect `expires_in`, and obtain a new token with the same client credentials before expiry. Coordinate renewal within the instance to avoid parallel refresh races. One authentication failure may trigger one renewal and bounded retry; repeated denial becomes an actionable authentication/access failure. No interactive login, password, browser cookies or human consent flow is needed at job runtime. Do not create a Secret Manager version for every temporary access token. Secret rotation changes the referenced credential value; temporary tokens and client secrets never enter payload bodies, reports or agent workspaces. Codex subscription OAuth renewal remains Deltahub-owned and separate.

## Limits and deadlines

Defaults: four reviewers; two concurrent agents; two additional failed-stage attempts; 30 minutes cumulative quota waiting; two hours total execution time. Reserve finalization time before the platform timeout. The overall deadline includes investigation, tools, retries, setup, quota waiting, publication and reporting.

`limits.agent_attempt_timeout_seconds` sets a positive work timeout for each role: history import, triage, reviewer, deduplication, verification and discussion. Each attempt is bounded by both that role limit and the remaining execution time minus finalization reserve. Track elapsed work time including tool execution; pause the role work clock only during explicit coordinated quota waiting. Quota waiting still consumes the execution deadline and cumulative quota allowance. Quiet reasoning or a long tool is not a failure merely because no output arrived.

An attempt timeout is `stage_timeout`, consumes one failed-stage attempt, and follows the existing bounded retry policy if execution time remains. A fresh attempt gets its role allowance but never extends the job deadline. Child processes are stopped on timeout. Setup/tool/network operations must also be bounded by remaining execution time. History import uses explicit models.history_import and limits.agent_attempt_timeout_seconds.history_import settings. They may initially match discussion settings, but changes to discussion do not implicitly change import. Verification includes final reply composition within its work timeout in both modes. Role-specific durations are deployment settings to tune during the POC; values in examples are illustrative, not agreed product limits.

Set Cloud Run task `max_retries = 0` explicitly. One execution has one worker attempt; there are no platform task restarts in this POC. The worker retries individual agents/transient operations inside the execution. A failed execution is retried by Deltahub as a new job record linked to the original and immediate predecessor, with a new execution/attempt ID and the same `request_id` only for unchanged input. The retry worker checks durable artifacts and restarts only unfinished/incompatible work. Deltahub owns timing, including waiting until subscription quota is expected to recover. New jobs receive new execution and ordinary failed-stage retry budgets. The human-import omission-correction pass allowance is the explicit exception: its consumed/pending passes persist across exact-input retries, as defined in [the workflow](agent-workflow.md#import-accounting-and-omission-correction), so a retry cannot restart that correction loop. Preserve earlier attempts for audit rather than erasing their history.

## Cancel, stop, and worker loss

Deltahub **cancel** removes a job during pre-flight states through enqueued, before it starts. No worker execution needs a stop signal. Deltahub **stop** applies after a job has started and before its terminal state. Deltahub records stop intent, then invokes Cloud Run's execution-cancellation API; the platform calls this operation “cancel,” but the application's command remains “stop.” Handle the enqueue/start race in Deltahub so a started execution is not left running after a pre-flight cancellation request.

The worker handles `SIGTERM` by refusing new work/retries, stopping Codex sessions and child processes, preserving available completed work, attempting bounded cleanup/reporting, and exiting. Use an entrypoint that delivers signals to the orchestrator rather than swallowing them in a shell. Cleanup time is limited and final callbacks/uploads are best-effort. A signal alone does not establish user intent: platform timeout can also send SIGTERM. Use recorded stop intent and platform execution outcome to distinguish stop from timeout/failure. Stops do not automatically trigger retries.

An intentional stop before computation finishes has null verdict and stopped execution/computation status. A stop after computation finishes preserves the computed result, with execution stopped and publication potentially pending/partial. In either case the durable checkpoints remain available. A pre-flight cancellation has no worker-generated report. Deltahub owns its terminal state names; the report/event `stopped` value records the worker's corresponding outcome.

When the orchestrator remains operational it handles agent crashes, failed operations and cleanup. If the instance disappears, the orchestrator dies, or forced termination prevents reporting, Deltahub only needs to observe the failed execution, record job failure and arrange a linked retry. It does not inspect findings or determine how far computation got. The next worker reconciles checkpoints and remote writes, whether recovery begins at 0% or 99%. Silence or absence of a callback alone is not proof of success; terminal execution status and Deltahub's stop intent establish the operational outcome.

Deltahub may close an abandoned `in_progress` GitHub Check with an operational failure/stop explanation. It must not overwrite an already completed Check solely because the job later failed. Persist the Check identity and immediately send `check_registered` with ownership metadata as soon as it is acknowledged; if the worker died before saving it, reconcile deterministic publication markers. Guard updates by job/review identity so an old failure notification cannot overwrite a Check already resumed or completed by a retry. The recovery worker owns review progress and publication reconciliation.

## Checkpoints

Write completed outputs and progress manifests to GCS as stages finish. Publish the artifact first and its checkpoint reference second. Include input digest, code identity, stage configuration/runtime versions, content digest, and completion status. Use object-generation preconditions or equivalent compare-and-swap protection for shared progress pointers.

Incremental persistence is mandatory during normal execution, not deferred until final report creation or shutdown. Persist each successful reviewer output and verifier batch independently, even while other agents are still running. Checkpoint other completed stages, retry/quota budget consumption, and publication progress as they occur. Persist publication intent before a remote write and acknowledged object IDs afterward, so recovery can reconcile a write whose acknowledgment was lost. Do not advance a dependent stage on the assumption that an unsaved result is recoverable.

A stop request or platform termination may leave only a short shutdown window, and a crash may leave none. The signal handler stops new work, terminates child processes, and attempts bounded cleanup, persistence, and reporting; successful final uploads or callbacks are not guaranteed. Recovery must remain possible from checkpoints already stored before the signal. Incremental persistence does not require saving unfinished agent reasoning or restoring an agent mid-turn; unfinished work restarts from its saved inputs.

On retry, verify artifacts and compatibility before reuse. A reviewer with `findings: []` is still a completed checkpoint. Restart an unfinished reviewer or verifier batch from its saved inputs. Do not depend on transferring in-memory agent state, process state, open sockets, or a copied worktree. Persist optional Codex session artifacts only as an implementation enhancement, never as the sole recovery path.

A crash loses work that has not reached durable storage. It does not erase stage artifacts already committed to GCS. A lost upload acknowledgment requires checking the artifact before repeating work.

## Recovery of abandoned reservations

A confirmed stopped/lost predecessor does not require an unwanted computation retry to release its report reservation. Use the authorized cleanup protocol in [contracts](contracts.md#abandoned-reservation-cleanup-without-resuming-the-request), preserving the original terminal report identity and recording the cleanup worker separately. Reconcile remote writes before clearing ownership. Recovery is restartable and bounded; it does not resume agents or unfinished publication after a stop. Latest saved report revision and latest completed assessment revision are separate pointers.

Human import omission correction additionally checkpoints its consumed pass budget, pending pass identity, stable source/finding allocations and the accounting/ledger transition. Exact-input retries resume a pending correction and cannot reset its consumed allowance. This bounded coverage repair uses stage_additional_attempts; see [the correction protocol](agent-workflow.md#import-accounting-and-omission-correction).

## Failure categories

| Failure | Handling | Review verdict |
| --- | --- | --- |
| Invalid input or disallowed configuration | Fail before agents; report field/reason | None |
| Required exact code unavailable | Fail, never review a substitute | None |
| Dependency/setup failure with readable source | Continue; record capability limitation | Determined by completed review |
| Optional context/attachment inaccessible | Record omission; investigate with available evidence | Determined by completed review |
| Reviewer/deduplicator/verifier unusable output or crash | Retry that stage; fail after allowance | None until all required stages complete |
| Quota cannot recover within allowance | Save completed work; report retry-later | None if computation unfinished |
| Specific assertion cannot be established/refuted | Completed verifier returns unverifiable with evidence gap | Severity/scope/lifecycle rules apply |
| Container crash/deadline | Deltahub records execution failure; a new retry worker reconciles durable artifacts | None if computation unfinished |
| GitHub delivery fails after computation | Preserve verdict; retry/reconcile delivery | Retained |
| Deltahub callback fails | Persist report/outbox event; retry within deadline; backend reconciles later | Retained if computed |
| New head/base appears | Continue publishing original review and note newer context | Original verdict retained |

No category called 'incomplete PR verdict' is introduced. Execution status, computed verdict, and delivery status are distinct.

## Observability

Record stage transitions, attempt counts, duration, quota waits, selected models/efforts, setup limitations, fetched-context provenance, findings/duplicates/verification counts, report revisions, and publication IDs. Include runtime-reported token usage when available. Missing data is unknown, not zero. Logs and artifacts must be redacted and access-controlled.

Retention periods and alert routing are deployment configuration. This specification does not invent a retention duration. GCS artifacts are private; GitHub links should lead to an authenticated report viewer or Deltahub job page, not make the bucket public.
