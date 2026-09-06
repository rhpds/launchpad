from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from app.services.catalog_certification import (
    build_certification_plan,
    evaluate_json_assertions,
    evaluate_promotion,
    load_certification_contract,
    score_rubric,
    validate_certification_contract,
    write_evidence_bundle,
)
from app.services.catalog_onboarding import load_intake

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "certification/catalog/multi-agent-quickstart.yaml"
INTAKE_PATH = ROOT / "catalog-onboarding/multi-agent-quickstart.yaml"


def _runner_module():
    path = ROOT / "scripts/catalog_certification.py"
    spec = importlib.util.spec_from_file_location("catalog_certification_cli", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_multi_agent_is_the_reference_reusable_certification_contract():
    contract = load_certification_contract(CONTRACT_PATH)
    intake = load_intake(INTAKE_PATH)

    assert validate_certification_contract(
        contract,
        intake=intake,
        repo_root=ROOT,
        contract_path=CONTRACT_PATH,
    ) == []
    assert contract["kind"] == "CatalogCertification"
    assert contract["metadata"]["catalog_item_id"] == "multi-agent-quickstart"
    assert contract["spec"]["kubeconfig_server"] == (
        "https://api.arena.fm2aihpcsed.com:6443"
    )
    assert [profile["seats"] for profile in contract["spec"]["scale_profiles"]] == [
        1,
        5,
        25,
    ]
    assert intake["certification"]["proof_contract"] == (
        "certification/catalog/multi-agent-quickstart.yaml"
    )


def test_twenty_five_seat_plan_is_one_order_on_one_cluster():
    contract = load_certification_contract(CONTRACT_PATH)
    intake = load_intake(INTAKE_PATH)

    plan = build_certification_plan(
        contract,
        intake=intake,
        seats=25,
        exposure_policy="internal",
    )

    assert plan["catalog_item_id"] == "multi-agent-quickstart"
    assert plan["cluster_ref"] == "arena"
    assert plan["kubeconfig_server"] == "https://api.arena.fm2aihpcsed.com:6443"
    assert plan["workshop_orders"] == 1
    assert plan["seats"] == 25
    assert plan["seat_probe_count"] == 25
    assert plan["all_seats_same_cluster"] is True
    assert plan["provision_concurrency"] == 2
    assert plan["probe_concurrency"] == 10
    assert plan["required_consecutive_runs"] == 3
    assert plan["showroom_pages_per_seat"] == 4
    assert plan["current_certified_seats"] == 1
    assert plan["next_promotion_target"] == 5
    assert plan["execution_eligible"] is False


def test_only_the_next_uncertified_scale_profile_can_execute():
    contract = load_certification_contract(CONTRACT_PATH)
    intake = load_intake(INTAKE_PATH)

    one = build_certification_plan(
        contract, intake=intake, seats=1, exposure_policy="internal"
    )
    five = build_certification_plan(
        contract, intake=intake, seats=5, exposure_policy="internal"
    )

    assert one["execution_eligible"] is True
    assert one["certification_override"] is False
    assert five["execution_eligible"] is True
    assert five["certification_override"] is True
    assert five["next_promotion_target"] == 5


def test_contract_rejects_unsafe_or_nonrepeatable_configuration():
    contract = load_certification_contract(CONTRACT_PATH)
    intake = load_intake(INTAKE_PATH)
    broken = deepcopy(contract)
    broken["spec"]["target_cluster"] = ""
    broken["spec"]["scale_profiles"] = [
        broken["spec"]["scale_profiles"][1],
        broken["spec"]["scale_profiles"][0],
    ]
    broken["spec"]["seat_probe"]["argv"] = ["/bin/sh", "-c", "echo unsafe"]
    broken["spec"]["showroom"]["pages"][0]["path"] = "relative/path"

    errors = validate_certification_contract(
        broken,
        intake=intake,
        repo_root=ROOT,
        contract_path=CONTRACT_PATH,
    )

    assert any("target_cluster" in error for error in errors)
    assert any("scale_profiles" in error for error in errors)
    assert any("shell execution" in error for error in errors)
    assert any("absolute URL path" in error for error in errors)


def test_structural_json_assertions_do_not_compare_model_prose():
    contract = load_certification_contract(CONTRACT_PATH)
    assertions = contract["spec"]["seat_probe"]["json_assertions"]
    assert assertions[0] == {
        "path": "result",
        "equals": "GREEN-live-internal-seat",
    }
    result = {
        "result": "GREEN-live-internal-seat",
        "cluster_ref": "arena",
        "readiness": {"agents_discovered": 3, "agents_expected": 3},
        "multi_agent_journey": {
            "steps": 3,
            "mcp_steps": ["research", "analyst", "executor"],
            "errors": [],
            "answer": "Nondeterministic model prose is intentionally ignored.",
        },
        "guardrails": {"blocked_steps": ["research", "analyst", "executor"]},
        "terminal_scope": [
            "project=seat-namespace",
            "own_edit=yes",
            "cross_namespace=DENIED",
            "node_list=DENIED",
        ],
        "contains_sensitive_values": False,
    }

    assert evaluate_json_assertions(result, assertions) == []
    result["multi_agent_journey"]["errors"] = ["failed"]
    failures = evaluate_json_assertions(result, assertions)
    assert any("multi_agent_journey.errors" in failure for failure in failures)


def test_rubric_and_promotion_fail_closed_until_every_gate_and_run_passes():
    contract = load_certification_contract(CONTRACT_PATH)
    gates = {
        gate
        for category in contract["spec"]["rubric"]["categories"]
        for gate in category["requires"]
    }
    green = score_rubric(contract, {gate: True for gate in gates})
    red = score_rubric(
        contract,
        {gate: gate != "zero_residue_cleanup" for gate in gates},
    )

    assert green["score"] == green["required"] == 100
    assert green["passed"] is True
    assert red["score"] < 100
    assert red["passed"] is False
    assert evaluate_promotion(contract, seats=25, recent_results=[True, True]) == {
        "required_consecutive_runs": 3,
        "consecutive_passing_runs": 2,
        "eligible": False,
    }
    assert evaluate_promotion(contract, seats=25, recent_results=[True, True, True])[
        "eligible"
    ] is True


def test_evidence_bundle_is_sanitized_and_hashed(tmp_path: Path):
    evidence = {
        "schema": "launchpad.redhat.com/catalog-certification-evidence/v1",
        "result": "GREEN-live",
        "api_key": "must-not-survive",
        "nested": {"access_code": "must-not-survive", "safe": "kept"},
    }
    path = tmp_path / "run.json"

    checksum_path = write_evidence_bundle(path, evidence)
    saved = json.loads(path.read_text())
    expected, filename = checksum_path.read_text().strip().split("  ", maxsplit=1)

    assert saved["api_key"] == "[REDACTED]"
    assert saved["nested"]["access_code"] == "[REDACTED]"
    assert saved["nested"]["safe"] == "kept"
    assert filename == path.name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_cli_plan_is_machine_readable_and_non_mutating():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/catalog_certification.py"),
            "plan",
            str(CONTRACT_PATH),
            "--intake",
            str(INTAKE_PATH),
            "--seats",
            "25",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    plan = json.loads(result.stdout)
    assert plan["workshop_orders"] == 1
    assert plan["seats"] == 25
    assert plan["cluster_ref"] == "arena"
    assert plan["mutates_cluster"] is False


def test_api_transport_does_not_shadow_the_session_lookup_method():
    runner = _runner_module()

    client = runner.LaunchpadApi("https://launchpad.example", "not-a-real-key")

    assert callable(client.session)


def test_generic_runner_places_probes_after_the_all_seat_barrier_and_reclaims(
    tmp_path: Path, monkeypatch, capsys
):
    runner = _runner_module()
    calls: list[str] = []
    sessions_fetched: set[str] = set()

    class FakeApi:
        def __init__(self, *_args, **_kwargs):
            pass

        def capacity_preview(self, body):
            calls.append("capacity")
            return {"can_provision": True, "selected_cluster": "arena"}

        def create_order(self, body, *, idempotency_key):
            calls.append("create")
            assert body["num_users"] == 5
            assert body["certification_override"] is True
            assert idempotency_key.endswith(":repeatable-five")
            return {"workshop_id": "workshop-1", "cluster_ref": "arena"}

        def confirm(self, workshop_id):
            calls.append("confirm")
            assert workshop_id == "workshop-1"
            return {"status": "queued"}

        def workshop(self, workshop_id):
            assert workshop_id == "workshop-1"
            if "reclaim" in calls:
                return {"status": "completed", "cluster_ref": "arena", "seats": []}
            return {
                "status": "ready",
                "cluster_ref": "arena",
                "seats": [
                    {
                        "seat_id": f"seat-{seat}",
                        "seat_number": seat,
                        "session_id": f"session-{seat}",
                        "status": "ready",
                        "showroom_url": f"https://seat-{seat}.example",
                    }
                    for seat in range(1, 6)
                ],
            }

        def session(self, session_id):
            sessions_fetched.add(session_id)
            reclaimed = "reclaim" in calls
            return {
                "session_id": session_id,
                "namespace": session_id.replace("session", "namespace"),
                "cluster_ref": "arena",
                "status": "reclaimed" if reclaimed else "ready",
                "maas_api_key": "" if reclaimed else "masked",
            }

        def reclaim(self, workshop_id):
            calls.append("reclaim")
            return {"status": "reclaiming"}

    def fake_seat_probe(*, seat, session, contract, verify):
        assert len(sessions_fetched) == 5
        return {
            "seat_number": seat["seat_number"],
            "showroom": [
                {"id": page["id"], "passed": True}
                for page in contract["spec"]["showroom"]["pages"]
            ],
            "probe": {
                "passed": True,
                "assertion_failures": [],
                "result": {
                    "terminal_scope": [
                        "own_edit=yes",
                        "cross_namespace=DENIED",
                        "node_list=DENIED",
                    ],
                    "contains_sensitive_values": False,
                },
            },
        }

    monkeypatch.setattr(runner, "LaunchpadApi", FakeApi)
    monkeypatch.setattr(runner, "_seat_probe", fake_seat_probe)
    monkeypatch.setattr(
        runner,
        "_kubeconfig_server",
        lambda _kubeconfig: "https://api.arena.fm2aihpcsed.com:6443",
    )
    monkeypatch.setattr(
        runner,
        "_resource_counts",
        lambda resources, **_kwargs: {resource: 0 for resource in resources},
    )
    monkeypatch.setattr(
        runner,
        "_git_value",
        lambda *args: "a" * 40 if args == ("rev-parse", "HEAD") else "",
    )
    monkeypatch.setenv("TEST_LAUNCHPAD_API_KEY", "not-a-real-key")
    monkeypatch.setenv("KUBECONFIG", str(tmp_path / "arena-kubeconfig"))
    output = tmp_path / "evidence" / "five-seat.json"
    args = SimpleNamespace(
        contract=str(CONTRACT_PATH),
        intake=str(INTAKE_PATH),
        seats=5,
        exposure_policy="internal",
        api_key_env="TEST_LAUNCHPAD_API_KEY",
        api_base_url="https://launchpad.example/api/v1",
        tenant_id="certification-tenant",
        owner_id="proof-runner",
        ttl="2h",
        run_id="repeatable-five",
        output=str(output),
        poll_interval=0.001,
        ca_bundle=None,
        insecure=False,
        allow_dirty=True,
    )

    assert runner._run_command(args) == 0
    evidence = json.loads(output.read_text())

    assert calls == ["capacity", "create", "confirm", "reclaim"]
    assert len(evidence["seat_results"]) == 5
    assert evidence["result"] == "GREEN-live"
    assert evidence["rubric"]["score"] == 100
    assert evidence["cleanup"]["status"] == "completed"
    assert set(evidence["proof_strategy"]) == {"TDD", "EDD", "CDD", "BDD", "CBT"}
    assert all(
        status == "GREEN-live" for status in evidence["validation_matrix"].values()
    )
    assert all(count == 0 for count in evidence["cleanup"]["resource_counts"].values())
    assert output.with_name(output.name + ".sha256").is_file()
    assert "not-a-real-key" not in capsys.readouterr().out
