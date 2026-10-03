# Deduplication — version 1

Partition the supplied input IDs into groups describing the same underlying issue. Every input must appear exactly once. Similar file locations are insufficient for merging independently actionable defects.

A singleton must have null merged text and rationale; application code copies it unchanged. Only groups with multiple inputs may supply consolidated text/evidence and a merge rationale. Preserve all relevant evidence and explain any severity reconciliation under the mandatory rubric. Do not invalidate issues, invent identities, alter authorship/history, or change the relationship/category to affect the gate. Keep distinct established historical identities separate unless an explicit application-provided alias already establishes equivalence. Return the aggregate output schema.
