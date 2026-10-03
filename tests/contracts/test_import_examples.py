"""Positive custom-policy and human-import accounting examples."""

from tests.support import contract_checks as checks


def test_history_import_customization_is_independent_from_discussion():
    inp = checks.read("custom-prompts-history-import-input")
    checks.stage_prompt(inp)
    assert inp["prompt"]["replacement_ref"]["prompt_id"] == "customer-history-import"
    assert "DISCUSSION_ONLY_SENTINEL" not in inp["prompt"]["text"]
    assert "IMPORT_ONLY_SENTINEL" in inp["prompt"]["text"]
    config = checks.read("custom-prompts-history-import-request")["config"]
    assert config["models"]["history_import"] != config["models"]["discussion"]
    timeouts = config["limits"]["agent_attempt_timeout_seconds"]
    assert timeouts["history_import"] != timeouts["discussion"]


def test_corrected_import_is_accounted_for_and_accepted_by_owner():
    checks.corrected_accounting(
        checks.read("history-import-correction-input"),
        checks.read("history-import-correction-output"),
        checks.read("import-accounting-corrected"),
    )
    checks.reviewer_ready(
        checks.read("import-corrected-reviewer-input"),
        checks.read("import-corrected-reviewer-output"),
    )
