"""Contract rejection cases; each mutation gets a fresh canonical example."""

import pytest
from jsonschema import ValidationError

from tests.support import contract_checks as checks


@pytest.mark.parametrize(
    "example_name, mutate, check",
    [
        pytest.param(
            "review-request",
            lambda d: d.update(job_id="changing-job"),
            lambda d: checks.validate("review-request", d),
            id="job_id_in_request",
        ),
        pytest.param(
            "review-request",
            lambda d: d["config"]["prompt_customizations"].update(
                mandatory={"replacement": None, "additions": []}
            ),
            lambda d: checks.validate("review-request", d),
            id="mandatory_prompt_replacement",
        ),
        pytest.param(
            "review-request",
            lambda d: d["config"]["limits"]["agent_attempt_timeout_seconds"].update(reviewer=0),
            lambda d: checks.validate("review-request", d),
            id="zero_reviewer_timeout",
        ),
        pytest.param(
            "review-request",
            lambda d: d["credentials"].pop("github_private_key_secret_ref"),
            lambda d: checks.validate("review-request", d),
            id="missing_github_key",
        ),
        pytest.param(
            "custom-prompts-reviewer-input",
            lambda d: d["prompt"].update(text="Replacement without mandatory policy"),
            lambda d: checks.prompt(d["prompt"]),
            id="replacement_without_mandatory_policy",
        ),
        pytest.param(
            "metadata-only-request",
            lambda d: d["context"]["sources"].pop(),
            lambda d: checks.context_sources(d["context"]),
            id="unresolved_source_id",
        ),
        pytest.param(
            "review-request",
            lambda d: d["context"]["sources"].append(d["context"]["documents"][0]["source"]),
            lambda d: checks.context_sources(d["context"]),
            id="duplicate_source_metadata",
        ),
        pytest.param(
            "review-request",
            lambda d: d["context"]["documents"][0].update(text="conflicting requirements"),
            lambda d: checks.context_sources(d["context"]),
            id="conflicting_duplicate_text",
        ),
        pytest.param(
            "review-request",
            lambda d: d["credentials"].update(jira_auth="password"),
            lambda d: checks.validate("review-request", d),
            id="jira_password_auth",
        ),
        pytest.param(
            "review-request",
            lambda d: d["credentials"].pop("jira_cloud_id"),
            lambda d: checks.validate("review-request", d),
            id="missing_jira_cloud_id",
        ),
        pytest.param(
            "review-request",
            lambda d: d["credentials"].pop("jira_credential_ref"),
            lambda d: checks.validate("review-request", d),
            id="missing_jira_credential",
        ),
        pytest.param(
            "review-request",
            lambda d: d["config"]["limits"].update(max_reverification_rounds=1),
            lambda d: checks.validate("review-request", d),
            id="removed_reverification_setting",
        ),
        pytest.param(
            "review-request",
            lambda d: d["config"]["models"].pop("history_import"),
            lambda d: checks.validate("review-request", d),
            id="missing_import_model",
        ),
        pytest.param(
            "review-request",
            lambda d: d["config"]["limits"]["agent_attempt_timeout_seconds"].update(
                history_import=0
            ),
            lambda d: checks.validate("review-request", d),
            id="zero_import_timeout",
        ),
    ],
)
def test_rejects_invalid_contract(example_name, mutate, check):
    value = checks.read(example_name)
    mutate(value)
    with pytest.raises((ValueError, ValidationError)):
        check(value)
