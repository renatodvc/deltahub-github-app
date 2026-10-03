"""Reference contract assertions, not production validation or worker behavior.

Migrated unchanged from the original specification validator. Tests of future
worker code must call that code, rather than duplicating it here.
"""

import hashlib
import json
import re

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from scripts.bundle_agent_schema import ROOT

SCHEMAS = {p.name: json.loads(p.read_text()) for p in (ROOT / "schemas").glob("*.json")}
REGISTRY = Registry().with_resources(
    (s["$id"], Resource.from_contents(s)) for s in SCHEMAS.values()
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(name):
    return json.loads((ROOT / "examples" / (name + ".json")).read_text())


def digest(name):
    return hashlib.sha256((ROOT / "examples" / (name + ".json")).read_bytes()).hexdigest()


def validate(schema, value):
    Draft202012Validator(
        SCHEMAS[schema + ".schema.json"], registry=REGISTRY, format_checker=FormatChecker()
    ).validate(value)


def walk(value):
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def unique(values, message):
    require(len(values) == len(set(values)), message)


def context_sources(ctx):
    records = ctx["sources"] + [d["source"] for d in ctx["documents"]]
    unique([s["source_id"] for s in records], "duplicate source metadata")
    by_id = {s["source_id"]: s for s in records}
    documents = {d["source"]["source_id"]: d["text"] for d in ctx["documents"]}
    entities = [
        ctx["pr"],
        ctx["jira_ticket"],
        *ctx["reviews"],
        *ctx["pr_comments"],
        *ctx["jira_ticket"]["comments"],
        *(c for thread in ctx["review_threads"] for c in thread["comments"]),
    ]
    for entity in entities:
        sid = entity["source_id"]
        require(sid in by_id, "typed source does not resolve")
        require(
            bool(by_id[sid]["uri"]) and bool(by_id[sid]["observed_at"]), "missing source provenance"
        )
        if sid in documents:
            require(
                documents[sid] == entity.get("body", entity.get("description")),
                "duplicate text differs",
            )


def coordination(d):
    r = d["active_reservation"]
    last = d["last_completed_revision"]
    require(last is None or 1 <= last <= d["last_saved_revision"], "completed revision pointer")
    require(d["recovery"] is None or r is not None, "recovery without reservation")
    if d["recovery"] is not None:
        require(
            d["recovery"]["predecessor_execution_id"] == r["execution_id"],
            "wrong recovery predecessor",
        )
    if r is not None:
        require(
            r["report_revision"] == d["last_saved_revision"] + 1,
            "reservation must allocate next revision",
        )
        require(
            r["expected_report_revision"] == (d["last_saved_revision"] or None),
            "reservation expected predecessor",
        )


def event(d):
    if d["kind"] == "delivery_failed" and d["report"] is None:
        require(
            d["checkpoint"] is not None
            and d["report_artifact"] is None
            and d["failure"]["code"] == "artifact_io_failed",
            "checkpoint-only delivery failure",
        )
    if d["kind"] == "authoritative_context_changed":
        require(
            d["context_change"]["policy"] == "continue_snapshot"
            and d["context_change"]["new_request_required"],
            "changed requirement policy",
        )
    if d["report"] is not None:
        r = d["report"]
        require(
            d["expected_report_revision"] == r["reservation"]["expected_report_revision"],
            "event revision precondition",
        )
        for key in ("job_id", "request_id", "review_id", "execution_id", "attempt_id"):
            require(d[key] == r[key], "event/report identity mismatch")
        if d["kind"] == "delivery_failed":
            if r["delivery_failure"] is None:
                require(
                    r["execution_status"] == "completed"
                    and d["failure"]["code"] == "deltahub_delivery_failed",
                    "unrecorded failure must be a later callback observation",
                )
            else:
                require(
                    d["failure"] == r["delivery_failure"], "delivery event/report cause mismatch"
                )
    if d["check"] is not None:
        check = d["check"]
        require(
            check["owner_job_id"] == d["job_id"]
            and check["owner_execution_id"] == d["execution_id"]
            and check["review_id"] == d["review_id"],
            "Check ownership mismatch",
        )


def assessment(a):
    require(bool(a["evidence"]) and bool(a["reason"].strip()), "assessment needs evidence/reason")
    if a["status"] == "invalid":
        require(
            a["invalid_reason"] in ("refuted", "fixed_in_reviewed_code", "requirements_changed"),
            "invalid requires a reason",
        )
    else:
        require(a["invalid_reason"] is None, "non-invalid assessment reason must be null")
    if a["status"] == "unverifiable":
        require(
            bool(a["missing_evidence"]) and bool(a["resolution_needed"]),
            "unverifiable needs evidence gap",
        )


def finding(f):
    require(
        bool(f["title"].strip()) and bool(f["body"].strip()) and bool(f["evidence"]),
        "empty finding",
    )
    if f["category"] in ("requirements", "scope", "language", "internal_reference"):
        require(f["severity"] == "major", "mandatory severity is major")
    if f["category"] == "custom_rule":
        require(f["severity"] == "blocking" and bool(f["rule_id"]), "custom rule severity/ID")
    else:
        require(f["rule_id"] is None, "non-custom finding rule ID must be null")
    require(
        f["primary_location"] is None or f["primary_location"] in f["locations"],
        "primary location missing",
    )


def closed_decisions(decisions, ledger):
    unique([d["finding_id"] for d in decisions], "duplicate closed finding decision")
    require(
        {d["finding_id"] for d in decisions}
        == {h["finding_id"] for h in ledger if h["lifecycle"] in ("fixed", "dismissed")},
        "closed finding decision coverage",
    )
    for d in decisions:
        require(bool(d["reason"].strip()), "closed finding decision needs reason")
        if d["decision"] == "reassess":
            require(bool(d["change_evidence"]), "reassessment needs change evidence")


def assessment_bindings(inp):
    entries = inp["assessment_bindings"]
    unique([b["finding_id"] for b in entries], "duplicate bound finding")
    unique([b["candidate_id"] for b in entries], "duplicate bound candidate")
    candidates = {c["candidate_id"]: c for c in inp["candidates"]}
    require(len(candidates) == len(inp["candidates"]), "duplicate canonical candidate")
    require(all(b["candidate_id"] in candidates for b in entries), "unknown bound candidate")
    expected = {h["finding_id"] for h in inp["history_ledger"] if h["requires_assessment"]}
    derived = {}
    for candidate_id, candidate in candidates.items():
        history_ids = [
            x.removeprefix("history:")
            for x in candidate["source_input_ids"]
            if x.startswith("history:")
        ]
        require(len(history_ids) <= 1, "multiple historical identities in one canonical candidate")
        for finding_id in history_ids:
            require(
                finding_id in expected and finding_id not in derived,
                "unknown/duplicate history membership",
            )
            require(
                candidate["finding"].get("existing_finding_id", finding_id) == finding_id,
                "canonical finding identity disagrees with membership",
            )
            derived[finding_id] = candidate_id
    supplied = {b["finding_id"]: b["candidate_id"] for b in entries}
    require(
        set(derived) == expected and supplied == derived,
        "binding disagrees with canonical source membership",
    )
    return supplied


def reply_coverage(targets, replies):
    unique([t["reply_target_id"] for t in targets], "duplicate reply target")
    by_id = {t["reply_target_id"]: t for t in targets}
    unique([r["reply_target_id"] for r in replies], "duplicate final reply")
    expected = {t["reply_target_id"] for t in targets}
    require({r["reply_target_id"] for r in replies} == expected, "reply target coverage")
    for reply in replies:
        target = by_id[reply["reply_target_id"]]
        require(reply["finding_id"] == target["finding_id"], "reply finding mismatch")
        require(bool(reply["body"].strip()), "empty reply")
        if "source_comment_ids" in reply:
            require(
                set(reply["source_comment_ids"]) == set(target["source_comment_ids"]),
                "reply source mismatch",
            )
    return by_id


def may_reactivate(issue, closure):
    return closure["relevant_change_confirmed"] and issue["status"] in ("valid", "unverifiable")


def verified_actions(inp, out):
    """Representative deterministic mapping, not the production orchestration/publisher."""
    by_finding = assessment_bindings(inp)
    assessments = {a["candidate_id"]: a for a in out["assessments"]}
    closures = {c["finding_id"]: c for c in out["closure_assessments"]}
    ledger = {h["finding_id"]: h for h in inp["history_ledger"]}
    actions = {}
    for fid, cid in by_finding.items():
        a = assessments[cid]
        if ledger[fid]["lifecycle"] != "open":
            actions[fid] = (
                "reactivate"
                if fid in closures and may_reactivate(a, closures[fid])
                else "retain_closure"
            )
        elif a["status"] == "invalid":
            actions[fid] = (
                "mark_fixed" if a["invalid_reason"] == "fixed_in_reviewed_code" else "invalidate"
            )
        else:
            actions[fid] = "confirm" if a["status"] == "valid" else "leave_unverifiable"
    return actions


def import_accounting(accounting, ledger=None):
    units = {u["source_unit_id"]: u for u in accounting["source_units"]}
    unique(
        [u["source_unit_id"] for u in accounting["source_units"]], "duplicate accounted source unit"
    )
    for u in units.values():
        require(bool(u["comment_source_ids"]), "empty import source unit")
        unique(u["comment_source_ids"], "duplicate unit comment")
    result = accounting["result"]
    agent("history-import", result)
    if not accounting["corrections"]:
        require(not result["omission_resolutions"], "initial accounting has correction resolutions")
    require(
        set(units) == {e["source_unit_id"] for e in result["entries"]},
        "accounting omitted a source unit",
    )
    unique([e["source_unit_id"] for e in result["entries"]], "duplicate accounted entry")
    expected = {
        (e["source_unit_id"], f["candidate_id"]) for e in result["entries"] for f in e["findings"]
    }
    mappings = accounting["finding_bindings"]
    unique(
        [(b["source_unit_id"], b["import_candidate_id"]) for b in mappings],
        "duplicate import binding",
    )
    require(
        expected == {(b["source_unit_id"], b["import_candidate_id"]) for b in mappings},
        "import binding coverage",
    )
    require(
        accounting["revision"] == len(accounting["corrections"]) + 1,
        "accounting revision/correction mismatch",
    )
    require(
        [c["pass_number"] for c in accounting["corrections"]]
        == list(range(1, accounting["revision"])),
        "correction sequence",
    )
    for e in result["entries"]:
        require(bool(e["explanation"].strip()), "empty import accounting explanation")
        for f in e["findings"]:
            finding(f)
            require(
                any(
                    set(ev["source_ids"]) & set(units[e["source_unit_id"]]["comment_source_ids"])
                    for ev in f["evidence"]
                ),
                "import accounting lacks assertion source",
            )
    if ledger is not None:
        by_id = {h["finding_id"]: h for h in ledger}
        for b in mappings:
            require(b["finding_id"] in by_id, "accounted human finding missing from ledger")
            h = by_id[b["finding_id"]]
            require(
                h["candidate"]["origin"] == "human", "import correction changed human authorship"
            )
            require(
                set(h["candidate"]["origin_source_ids"])
                & set(units[b["source_unit_id"]]["comment_source_ids"]),
                "import provenance mismatch",
            )
            require(bool(h["thread_links"]), "import correction lost original thread")


def import_omissions(omissions, accounting):
    units = {u["source_unit_id"]: u for u in accounting["source_units"]}
    unique([o["omission_id"] for o in omissions], "duplicate omission ID")
    for o in omissions:
        require(o["source_unit_id"] in units, "unknown omission source unit")
        require(
            bool(o["comment_source_ids"])
            and set(o["comment_source_ids"])
            <= set(units[o["source_unit_id"]]["comment_source_ids"]),
            "foreign omission evidence",
        )
        unique(o["comment_source_ids"], "duplicate omission comment")
        require(
            all(o[k].strip() for k in ("omission_id", "assertion", "reason")),
            "empty omission explanation",
        )


def import_correction(inp, out):
    c = inp["correction"]
    if c is None:
        require(not out["omission_resolutions"], "initial import cannot resolve omissions")
        return
    prior = c["prior_accounting"]
    import_accounting(prior)
    import_omissions(c["omissions"], prior)
    require(bool(c["omissions"]), "empty correction request")
    require(
        c["pass_number"] == prior["revision"] and c["pass_number"] <= c["max_passes"],
        "correction allowance exhausted/reset",
    )
    require(
        {u["source_unit_id"] for u in inp["source_units"]}
        == {o["source_unit_id"] for o in c["omissions"]},
        "correction source-unit scope",
    )
    old_units = {u["source_unit_id"]: u for u in prior["source_units"]}
    require(
        all(u == old_units[u["source_unit_id"]] for u in inp["source_units"]),
        "correction changed pinned source unit",
    )
    old_entries = {e["source_unit_id"]: e for e in prior["result"]["entries"]}
    entries = {e["source_unit_id"]: e for e in out["entries"]}
    for uid, e in entries.items():
        before = {f["candidate_id"]: f for f in old_entries[uid]["findings"]}
        after = {f["candidate_id"]: f for f in e["findings"]}
        require(
            all(after.get(cid) == f for cid, f in before.items()),
            "correction removed/rewrote imported assertion",
        )
    resolutions = out["omission_resolutions"]
    unique([r["omission_id"] for r in resolutions], "duplicate omission resolution")
    require(
        {r["omission_id"] for r in resolutions} == {o["omission_id"] for o in c["omissions"]},
        "omission resolution coverage",
    )
    for r in resolutions:
        o = next(o for o in c["omissions"] if o["omission_id"] == r["omission_id"])
        before = {f["candidate_id"] for f in old_entries[o["source_unit_id"]]["findings"]}
        after = {f["candidate_id"] for f in entries[o["source_unit_id"]]["findings"]}
        require(bool(r["reason"].strip()), "omission resolution needs reason")
        unique(r["candidate_ids"], "duplicate resolution candidate")
        if r["outcome"] == "not_an_assertion":
            require(not r["candidate_ids"], "non-assertion linked to candidate")
        else:
            require(
                bool(r["candidate_ids"]) and set(r["candidate_ids"]) <= after,
                "unknown resolution candidate",
            )
            require(
                set(r["candidate_ids"]) <= before
                if r["outcome"] == "already_represented"
                else not (set(r["candidate_ids"]) & before),
                "wrong correction outcome",
            )


def corrected_accounting(inp, out, accepted):
    import_correction(inp, out)
    import_accounting(accepted)
    prior = inp["correction"]["prior_accounting"]
    require(
        accepted["accounting_id"] == prior["accounting_id"]
        and accepted["revision"] == prior["revision"] + 1,
        "correction changed accounting identity/revision",
    )
    require(
        accepted["source_units"] == prior["source_units"], "correction lost pinned source inventory"
    )
    expected = {e["source_unit_id"]: e for e in prior["result"]["entries"]}
    expected.update({e["source_unit_id"]: e for e in out["entries"]})
    require(
        {e["source_unit_id"]: e for e in accepted["result"]["entries"]} == expected,
        "correction did not preserve/merge exact entries",
    )
    require(
        accepted["result"]["omission_resolutions"] == out["omission_resolutions"],
        "correction lost latest dispositions",
    )
    require(
        all(b in accepted["finding_bindings"] for b in prior["finding_bindings"]),
        "correction rewrote stable bindings",
    )
    require(accepted["corrections"][:-1] == prior["corrections"], "correction lost history")


def reviewer_ready(inp, out):
    agent("reviewer", out, inp)
    if out["quality_control"] is not None:
        require(
            not out["quality_control"]["import_omissions"],
            "unresolved import omissions prevent reviewer completion",
        )


def agent(role, out, inp=None):
    for node in walk(out):
        if isinstance(node, dict) and "start_line" in node:
            require(
                node["start_line"] > 0 and node["end_line"] >= node["start_line"], "bad line range"
            )
    if role == "history-import":
        unique([e["source_unit_id"] for e in out["entries"]], "duplicate import unit")
        unique(
            [f["candidate_id"] for e in out["entries"] for f in e["findings"]],
            "duplicate imported candidate",
        )
        units = {u["source_unit_id"]: u for u in inp["source_units"]} if inp else None
        if units is not None:
            require(
                set(units) == {e["source_unit_id"] for e in out["entries"]},
                "missing/unknown import unit",
            )
        for entry in out["entries"]:
            require(bool(entry["explanation"].strip()), "import explanation missing")
            for f in entry["findings"]:
                finding(f)
                require(f["existing_finding_id"] is None, "import cannot relabel existing finding")
                if units is not None:
                    sources = {s for e in f["evidence"] for s in e["source_ids"]}
                    require(
                        bool(sources & set(units[entry["source_unit_id"]]["comment_source_ids"])),
                        "import lacks human source evidence",
                    )
        if inp:
            import_correction(inp, out)
    elif role == "reviewer":
        unique([f["candidate_id"] for f in out["findings"]], "duplicate candidate IDs")
        for f in out["findings"]:
            finding(f)
        q = out["quality_control"]
        if inp:
            require(
                (q is not None) == inp["assignment"]["owns_quality_control"],
                "quality ownership mismatch",
            )
            require(
                (inp["import_accounting"] is not None) == inp["assignment"]["owns_quality_control"],
                "missing/foreign import accounting",
            )
            if inp["import_accounting"] is not None:
                import_accounting(inp["import_accounting"], inp["history_ledger"])
        if q is not None:
            ids = [c["rule_id"] for c in q["custom_rules"]]
            unique(ids, "duplicate custom rules")
            if inp:
                require(
                    set(ids)
                    == set(inp["assignment"]["expected_custom_rule_ids"])
                    == {r["rule_id"] for r in inp["custom_rules"]},
                    "custom rule coverage mismatch",
                )
            if inp:
                closed_decisions(q["closed_finding_decisions"], inp["history_ledger"])
                require(
                    q["import_accounting_revision"] == inp["import_accounting"]["revision"],
                    "stale import accounting acknowledgment",
                )
                import_omissions(q["import_omissions"], inp["import_accounting"])
            for result in [*q["built_in"].values(), *q["custom_rules"]]:
                require(bool(result["explanation"].strip()), "quality explanation required")
                if result["result"] == "finding":
                    require(bool(result["candidate_ids"]), "quality finding needs candidate")
    elif role == "triage":
        require(bool(out["assignments"]), "empty triage")
        require(any(a["owns_quality_control"] for a in out["assignments"]), "no quality owner")
        if inp:
            require(len(out["assignments"]) <= inp["max_reviewers"], "reviewer cap")
            expected = {x["lens_id"] for x in inp["mandatory_lenses"]}
            actual = {x for a in out["assignments"] for x in a["mandatory_lens_ids"]}
            require(expected == actual, "lens coverage")
            require(
                all(a["model"] in inp["reviewer_choices"] for a in out["assignments"]),
                "model allowlist",
            )
    elif role == "aggregate":
        require(bool(out["groups"]), "empty candidate groups")
        ids = []
        for g in out["groups"]:
            require(bool(g["input_ids"]), "empty group")
            ids += g["input_ids"]
            if len(g["input_ids"]) == 1:
                require(
                    g["merged_text"] is None and g["merge_rationale"] is None, "singleton rewritten"
                )
            else:
                require(
                    g["merged_text"] is not None and bool(g["merge_rationale"]),
                    "merge lacks content/rationale",
                )
        unique(ids, "duplicate group source")
        if inp:
            require(
                set(ids) == {x["input_id"] for x in inp["candidates"]},
                "candidate partition mismatch",
            )
    elif role == "verifier":
        unique([a["candidate_id"] for a in out["assessments"]], "duplicate assessments")
        unique([r["reply_target_id"] for r in out["final_replies"]], "duplicate final reply")
        unique(
            [c["finding_id"] for c in out["closure_assessments"]], "duplicate closure assessment"
        )
        for a in out["assessments"]:
            assessment(a)
        for c in out["closure_assessments"]:
            require(
                bool(c["reason"].strip()) and bool(c["evidence"]),
                "closure assessment needs evidence",
            )
        for reply in out["final_replies"]:
            require(
                bool(reply["body"].strip()) and bool(reply["source_comment_ids"]),
                "reply needs body/source",
            )
        if inp:
            require(
                {a["candidate_id"] for a in out["assessments"]}
                == {a["candidate_id"] for a in inp["candidates"]},
                "assessment coverage",
            )
            by_finding = assessment_bindings(inp)
            expected = reply_coverage(inp["final_reply_targets"], out["final_replies"])
            if inp["purpose"] == "review":
                require(
                    not inp["proposed_reassessments"],
                    "review must use reviewer evidence, not a discussion investigator",
                )
            for reply in out["final_replies"]:
                require(reply["finding_id"] in by_finding, "reply for unassessed finding")
                h = next(h for h in inp["history_ledger"] if h["finding_id"] == reply["finding_id"])
                require(h["candidate"]["origin"] == "ai", "automatic reply to human finding")
            selected = {
                d["finding_id"]
                for d in inp["closed_finding_decisions"]
                if d["decision"] == "reassess"
            }
            closed_targets = {
                h["finding_id"]
                for h in inp["history_ledger"]
                if h["lifecycle"] != "open" and h["requires_assessment"]
            }
            if inp["purpose"] == "discussion":
                selected = closed_targets
                closed_decisions(
                    inp["closed_finding_decisions"],
                    [h for h in inp["history_ledger"] if h["finding_id"] in selected],
                )
            else:
                reply_closed = {
                    t["finding_id"] for t in inp["final_reply_targets"]
                } & closed_targets
                require(selected | reply_closed == closed_targets, "closed pool selection")
                selected |= reply_closed
                closed_decisions(inp["closed_finding_decisions"], inp["history_ledger"])
            require(
                selected == {c["finding_id"] for c in out["closure_assessments"]},
                "closure assessment coverage",
            )
            for a in out["assessments"]:
                if a["invalid_reason"] == "fixed_in_reviewed_code":
                    require(
                        any(
                            e["location"] and e["location"].get("revision_role") == "head"
                            for e in a["evidence"]
                        ),
                        "fix evidence is not reviewed head",
                    )
    elif role == "discussion":
        ids = [p["finding_id"] for p in out["proposed_reassessments"]]
        unique(ids, "duplicate discussion proposals")
        for p in out["proposed_reassessments"]:
            assessment(p["assessment"])
        if inp:
            overridden = {x["finding_id"] for x in inp["validated_dismissals"]}
            require(
                set(ids) == set(inp["target_finding_ids"]) - overridden,
                "technical proposal coverage",
            )
            closed_decisions(
                out["closed_finding_decisions"],
                [h for h in inp["history_ledger"] if h["finding_id"] in set(ids)],
            )


def historical(inp):
    seeded = {
        "history:" + h["finding_id"] for h in inp["history_ledger"] if h["requires_assessment"]
    }
    actual = {s for c in inp["candidates"] for s in c["source_input_ids"]}
    require(seeded <= actual, "historical candidate omitted")
    require(
        actual == {s["input_id"] for s in inp["source_candidates"]}, "original candidates missing"
    )


def prompt(p):
    manifest = json.loads((ROOT / "prompts/manifest.json").read_text())
    require(p["bundle_version"] == manifest["bundle_version"], "unknown prompt bundle")
    policy = (ROOT / "prompts" / manifest["policy"]["path"]).read_text().strip()
    require(p["text"].startswith(policy + "\n\n"), "mandatory policy missing/replaced")
    require(p["sha256"] == hashlib.sha256(p["text"].encode()).hexdigest(), "prompt digest mismatch")
    require(
        p["policy_ref"] == {k: manifest["policy"][k] for k in ("prompt_id", "version")},
        "policy provenance",
    )


def stage_prompt(d):
    manifest = json.loads((ROOT / "prompts/manifest.json").read_text())
    role = {
        "history-import": "history_import",
        "aggregate": "deduplication",
        "verifier": "verification",
    }.get(d["stage"], d["stage"])
    expected = {k: manifest["roles"][role][k] for k in ("prompt_id", "version")}
    require(d["prompt"]["base_ref"] == expected, "stage uses wrong base prompt")


def derived_actions_match(inp, out, actions):
    expected = verified_actions(inp, out)
    require(
        {a["finding_id"]: a["action"] for a in actions} == expected, "action contradicts verifier"
    )
    reply_coverage(
        inp["final_reply_targets"],
        [dict(r, finding_id=a["finding_id"]) for a in actions for r in a["proposed_replies"]],
    )
    accepted = {r["reply_target_id"]: r["body"] for a in actions for r in a["proposed_replies"]}
    require(
        accepted == {r["reply_target_id"]: r["body"] for r in out["final_replies"]},
        "action rewrites final reply",
    )


COMPUTATIONAL = {
    "triage",
    "reviewer",
    "deduplication",
    "verification",
    "discussion",
    "history_import",
    "composition",
}


def completion(r):
    unique([s["stage_id"] for s in r["stages"]], "duplicate stage record")
    unique(r["required_stage_ids"], "duplicate required stage")
    if r["review_status"] != "completed":
        return
    require(r["computation_plan"] is not None, "missing durable computation plan")
    stages = {s["stage_id"]: s for s in r["stages"]}
    require(bool(r["required_stage_ids"]), "completed review has no required plan")
    for stage_id in r["required_stage_ids"]:
        require(
            stage_id in stages and stages[stage_id]["status"] == "succeeded",
            "required stage missing or unsuccessful",
        )
    for stage in r["stages"]:
        if stage["kind"] in COMPUTATIONAL:
            require(
                stage["status"] in ("succeeded", "skipped"),
                "unfinished computational stage in completed report",
            )
            if stage["status"] == "succeeded":
                require(
                    stage["stage_id"] in r["required_stage_ids"],
                    "successful computation omitted from required plan",
                )
                require(
                    stage["completion_artifact"] is not None and stage["failure"] is None,
                    "no successful completion evidence",
                )
        if stage["reused_from"] is not None:
            reused = stage["reused_from"]
            require(
                stage["status"] == "succeeded"
                and stage["completion_artifact"] is not None
                and reused["completion_artifact"] == stage["completion_artifact"],
                "invalid completion reuse",
            )
            require(
                reused["stage_id"] == stage["stage_id"] and reused["job_id"] != r["job_id"],
                "reuse producer mismatch",
            )
    kinds = {stages[x]["kind"] for x in r["required_stage_ids"]}
    require("composition" in kinds, "missing composition stage")
    if r["mode"] == "review":
        require(r["triage"] is not None and "triage" in kinds, "missing triage completion")
        reviewer_ids = {a["reviewer_id"] for a in r["resolved_assignments"]}
        require(
            bool(reviewer_ids)
            and len(reviewer_ids)
            == len(r["resolved_assignments"])
            == len(r["triage"]["assignments"]),
            "reviewer plan mismatch",
        )
        actual = {
            s["stage_id"]
            for s in r["stages"]
            if s["kind"] == "reviewer" and s["stage_id"] in r["required_stage_ids"]
        }
        require(actual == reviewer_ids, "required reviewer missing from completion plan")
        if r["stats"]["dedup_input_count"] >= 2:
            require("deduplication" in kinds, "missing required deduplication")
        if r["stats"]["dedup_output_count"]:
            require("verification" in kinds, "missing required verification")
    elif r["technical_discussion_finding_ids"]:
        require({"discussion", "verification"} <= kinds, "missing two-agent discussion completion")
    if r["mode"] == "review":
        require(not r["technical_discussion_finding_ids"], "discussion scope in code review")
    if r["mode"] == "discussion":
        require(
            set(r["technical_discussion_finding_ids"])
            == {a["finding_id"] for a in r["finding_actions"] if a["action"] != "dismiss_by_human"},
            "technical discussion action coverage",
        )


def report(r):
    completion(r)
    for s in r["stages"]:
        if s["started_at"] and s["finished_at"]:
            require(
                s["started_at"] <= s["finished_at"] <= r["created_at"], "stage/report chronology"
            )
    for command in r["dismissals"]:
        require(command["observed_at"] <= r["created_at"], "report predates dismissal")
    fs, stats = r["findings"], r["stats"]
    active = [
        f
        for f in fs
        if f["verification"]
        and f["verification"]["status"] in ("valid", "unverifiable")
        and f["lifecycle"] == "open"
        and f["finding"]["relationship"] == "pr_related"
        and f["finding"]["severity"] in ("major", "blocking")
    ]
    expected = (
        None if r["review_status"] != "completed" else "requires_changes" if active else "approved"
    )
    require(r["verdict"] == expected, "verdict mismatch")
    if r["review_status"] == "completed":
        for q in r["quality_checks"]:
            require(
                not q["results"]["import_omissions"],
                "completed report has unresolved import omission",
            )
            require(
                q["results"]["import_accounting_revision"] >= 1, "invalid accepted import revision"
            )
    require(stats["raw_findings"] == len(r["raw_findings"]), "raw count mismatch")
    require(stats["canonical_findings"] == len(fs), "canonical count mismatch")
    require(stats["active_gate_findings"] == len(active), "gate count mismatch")
    require(
        stats["duplicates_removed"] == stats["dedup_input_count"] - stats["dedup_output_count"],
        "dedupe counts",
    )
    for status in ("valid", "invalid", "unverifiable"):
        require(
            stats[status + "_findings"]
            == sum(bool(f["verification"]) and f["verification"]["status"] == status for f in fs),
            "assessment counts",
        )
    if r["execution_status"] == "completed":
        require(r["publication"]["status"] == "complete", "execution complete before publication")
    reservation = r["reservation"]
    for key in ("request_id", "job_id", "execution_id", "report_revision"):
        require(reservation[key] == r[key], "reservation owner/revision mismatch")
    require(
        reservation["expected_report_revision"] == (r["report_revision"] - 1 or None),
        "reservation predecessor",
    )
    for f in fs:
        require(
            re.fullmatch(
                r"finding-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
                f["finding_id"],
            ),
            "non-global finding ID",
        )
        for item in r["publication"]["objects"]:
            if (
                item["finding_id"] == f["finding_id"]
                and item["kind"] == "inline_comment"
                and item["status"] == "published"
            ):
                require(
                    any(
                        link["github_id"] == item["github_id"] and link["url"] == item["url"]
                        for link in f["thread_links"]
                    ),
                    "published finding missing thread association",
                )
    reply_coverage(
        r["reply_targets"],
        [
            dict(p, finding_id=a["finding_id"])
            for a in r["finding_actions"]
            for p in a["proposed_replies"]
        ],
    )
    targets = {t["reply_target_id"]: t for t in r["reply_targets"]}
    for item in r["publication"]["objects"]:
        if item["kind"] == "reply":
            require(
                item["reply_target_id"] in targets
                and item["finding_id"] == targets[item["reply_target_id"]]["finding_id"],
                "publication reply target mismatch",
            )
            require(item["reply_to"] is not None, "reply destination missing")
        else:
            require(item["reply_target_id"] is None, "non-reply carries reply target")
    for a in r["finding_actions"]:
        if a["action"] == "dismiss_by_human":
            require(
                any(
                    c["finding_id"] == a["finding_id"]
                    and c["source_id"] in a["source_comment_ids"]
                    and c["actor"]["kind"] == "human"
                    and not c["actor"]["is_pr_author"]
                    for c in r["dismissals"]
                ),
                "dismissal has no authorized command",
            )
    for p in r["provenance"]["prompts"]:
        prompt(p)


def subset(s):
    allowed = {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "anyOf",
        "enum",
        "$defs",
        "$ref",
        "description",
        "title",
    }

    def check(node):
        require(
            set(node) <= allowed, "unsupported output-schema keyword: " + str(set(node) - allowed)
        )
        if node.get("type") == "object":
            require(set(node["required"]) == set(node["properties"]), "optional output property")
            require(node["additionalProperties"] is False, "open output object")
        if "$ref" in node:
            require(node["$ref"].startswith("#/$defs/"), "external bundled reference")
        for key in ("properties", "$defs"):
            for value in node.get(key, {}).values():
                check(value)
        if "items" in node:
            check(node["items"])
        for value in node.get("anyOf", []):
            check(value)

    check(s)
