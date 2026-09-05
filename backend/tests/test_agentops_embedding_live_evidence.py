from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-shared-embedding-live-2026-09-05.json"


def test_agentops_shared_embedding_live_evidence_is_complete_and_sanitized():
    payload = json.loads(EVIDENCE.read_text())

    assert payload["evidence_id"] == "LIVE-AGENTOPS-014"
    assert payload["repository_revision"] == ("b8dbb769127a82d6d8568f4d93f8dbb5b4084476")
    assert payload["cluster_id"] == "arena"
    assert payload["checks"]["health"]["status"] == "pass"
    assert payload["checks"]["embedding"]["dimensions"] == 768
    assert payload["checks"]["restart_from_cache"]["ready_seconds"] <= 60
    assert payload["checks"]["concurrent_burst"]["successful_requests"] == 25
    assert payload["checks"]["concurrent_burst"]["requested"] == 25
    assert payload["checks"]["network_isolation"]["public_route_created"] is False
    assert payload["checks"]["runtime_injection"]["status"] == "pass-live"
    assert payload["artifacts"]["arena_backend"]["build"] == "launchpad-backend-59"
    assert payload["security"]["secrets_included"] is False
    assert payload["result"] == "partial"
    assert "knowledge-base ingestion" in " ".join(payload["remaining_checks"])
