"""Contract rejection cases; each mutation gets a fresh canonical example."""

import pytest
from jsonschema import ValidationError

from tests.support import contract_checks as checks


def preserving_import_input():
    value = checks.read("history-import-correction-input")
    value["correction"]["prior_accounting"] = checks.read("import-accounting-corrected")
    value["correction"]["pass_number"] = 2
    return value


@pytest.mark.parametrize(
    "example_name, mutate, check",
    [
        pytest.param(
            "history-import-output",
            lambda d: d["entries"].pop(),
            lambda d: checks.agent("history-import", d, checks.read("history-import-input")),
            id="missing_import_unit",
        ),
        pytest.param(
            "history-import-output",
            lambda d: d["entries"][0]["findings"][0].update(origin="human"),
            lambda d: checks.validate("history-import-output", d),
            id="agent_supplied_human_origin",
        ),
        pytest.param(
            "history-import-output",
            lambda d: d["entries"][0]["findings"][0]["evidence"][0].update(source_ids=["invented"]),
            lambda d: checks.agent("history-import", d, checks.read("history-import-input")),
            id="invented_import_source",
        ),
        pytest.param(
            "history-import-input",
            lambda d: d.update(prompt=checks.read("discussion-input")["prompt"]),
            checks.stage_prompt,
            id="wrong_import_prompt_role",
        ),
        pytest.param(
            "import-omission-reviewer-input",
            lambda d: d.update(import_accounting=None),
            lambda d: checks.agent("reviewer", checks.read("import-omission-reviewer-output"), d),
            id="missing_import_accounting",
        ),
        pytest.param(
            "import-accounting-missed",
            lambda d: d["result"]["entries"].pop(),
            checks.import_accounting,
            id="missing_accounted_unit",
        ),
        pytest.param(
            "import-accounting-corrected",
            lambda d: d["finding_bindings"].clear(),
            checks.import_accounting,
            id="missing_import_binding",
        ),
        pytest.param(
            "import-omission-reviewer-output",
            lambda d: d["quality_control"]["import_omissions"][0].update(source_unit_id="unknown"),
            lambda d: checks.agent("reviewer", d, checks.read("import-omission-reviewer-input")),
            id="unknown_omission_unit",
        ),
        pytest.param(
            "import-omission-reviewer-output",
            lambda d: d["quality_control"]["import_omissions"][0].update(
                comment_source_ids=["foreign"]
            ),
            lambda d: checks.agent("reviewer", d, checks.read("import-omission-reviewer-input")),
            id="foreign_omission_comment",
        ),
        pytest.param(
            "import-omission-reviewer-output",
            lambda d: None,
            lambda d: checks.reviewer_ready(checks.read("import-omission-reviewer-input"), d),
            id="unresolved_omission_finishes_owner",
        ),
        pytest.param(
            "import-corrected-reviewer-output",
            lambda d: d["quality_control"].update(import_accounting_revision=1),
            lambda d: checks.reviewer_ready(checks.read("import-corrected-reviewer-input"), d),
            id="stale_accounting_revision",
        ),
        pytest.param(
            "history-import-correction-output",
            lambda d: d.update(omission_resolutions=[]),
            lambda d: checks.agent(
                "history-import", d, checks.read("history-import-correction-input")
            ),
            id="unresolved_import_correction",
        ),
        pytest.param(
            "history-import-correction-output",
            lambda d: d["omission_resolutions"][0].update(candidate_ids=["unknown"]),
            lambda d: checks.agent(
                "history-import", d, checks.read("history-import-correction-input")
            ),
            id="unknown_correction_candidate",
        ),
        pytest.param(
            "history-import-correction-input",
            lambda d: d["correction"].update(max_passes=0),
            lambda d: checks.agent(
                "history-import", checks.read("history-import-correction-output"), d
            ),
            id="zero_correction_allowance",
        ),
        pytest.param(
            "history-import-correction-input",
            lambda d: d["correction"].update(pass_number=2),
            lambda d: checks.agent(
                "history-import", checks.read("history-import-correction-output"), d
            ),
            id="exhausted_correction_allowance",
        ),
        pytest.param(
            "import-corrected-reviewer-input",
            lambda d: d["history_ledger"][0]["candidate"].update(origin="ai"),
            lambda d: checks.reviewer_ready(d, checks.read("import-corrected-reviewer-output")),
            id="imported_human_changed_to_ai",
        ),
        pytest.param(
            "import-corrected-reviewer-input",
            lambda d: d["history_ledger"][0].update(thread_links=[]),
            lambda d: checks.reviewer_ready(d, checks.read("import-corrected-reviewer-output")),
            id="imported_human_loses_thread",
        ),
        pytest.param(
            "history-import-correction-output",
            lambda d: d["entries"][0]["findings"].clear(),
            lambda d: checks.agent("history-import", d, preserving_import_input()),
            id="correction_deletes_existing_assertion",
        ),
        pytest.param(
            "import-accounting-corrected",
            lambda d: d["source_units"].pop(),
            lambda d: checks.corrected_accounting(
                checks.read("history-import-correction-input"),
                checks.read("history-import-correction-output"),
                d,
            ),
            id="correction_removes_source_unit",
        ),
        pytest.param(
            "import-accounting-corrected",
            lambda d: d["result"]["entries"][1].update(explanation="Unrelated rewrite"),
            lambda d: checks.corrected_accounting(
                checks.read("history-import-correction-input"),
                checks.read("history-import-correction-output"),
                d,
            ),
            id="correction_rewrites_unaffected_unit",
        ),
    ],
)
def test_rejects_invalid_contract(example_name, mutate, check):
    value = checks.read(example_name)
    mutate(value)
    with pytest.raises((ValueError, ValidationError)):
        check(value)
