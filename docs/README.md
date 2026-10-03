# Documentation map

The documents describe one agreed design. Start with the specification and read detailed references only for the area being implemented. Each reference below owns that area's rules; the decision register summarizes choices and accepted limitations. Schemas describe serialization, prompts guide agents, and examples illustrate behavior; none replaces the detailed semantic rules. When maintaining a rule, update its owning reference and affected contracts/examples, and link to it from summaries rather than creating another specification.

| Read for | Document |
| --- | --- |
| Scope, ownership, use cases, defaults, and overall flow | [Specification](specification.md) |
| Review stages, quality rules, human findings, discussion, and verdicts | [Agent workflow](agent-workflow.md) |
| Stage context, allowed tools, MCP transport, and authentication boundaries | [Agent inputs and tools](agent-inputs-and-tools.md) |
| Immutable payloads, identities, reports, events, revisions, and backend operations | [Contracts](contracts.md) |
| Schema structure and required semantic validation | [Validation rules](schema-validation.md) |
| Checkout/setup, isolation, credentials, deadlines, stop, and recovery | [Runtime and recovery](runtime-and-recovery.md) |
| Checks, comments, anchors, commit attribution, and repeatable publication | [GitHub publication](github-publication.md) |
| Implementation acceptance criteria and suggested delivery sequence | [Acceptance](acceptance.md) |
| Selected design, limitations, feasibility checks, and source references | [Decisions](decisions.md) |
| Test placement, fixtures, isolation, and contribution rules | [Testing guide](testing.md) |

For machine-readable contracts and runtime prompt assets, use the [schema index](../schemas/README.md) and [prompt bundle](../prompts/README.md). The [example catalog](../examples/README.md) illustrates the contracts; the [script guide](../scripts/README.md) explains local validation and schema preparation.

See the [team guide](../CONTRIBUTING.md) for setup and maintenance. The worker itself, deployment resources, and live integration tests remain to be implemented.
