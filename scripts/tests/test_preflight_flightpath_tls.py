import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from preflight_flightpath_tls import DEFAULT_HOSTS, _probe_host, evaluate


def test_default_preflight_covers_all_candidate_browser_routes() -> None:
    assert DEFAULT_HOSTS == (
        "launchpad-candidate.apps.flightpath.fm2aihpcsed.com",
        "launchpad-admin-candidate.apps.flightpath.fm2aihpcsed.com",
        "launchpad-api-candidate.apps.flightpath.fm2aihpcsed.com",
    )


def test_preflight_requires_trust_expiry_and_non_server_error() -> None:
    observations = {
        "trusted.example": {
            "host": "trusted.example",
            "trusted": True,
            "valid_for_days": 90,
            "http_status": 403,
        },
        "untrusted.example": {
            "host": "untrusted.example",
            "trusted": False,
            "failure": "certificate-verification-failed",
            "http_status": None,
        },
        "expiring.example": {
            "host": "expiring.example",
            "trusted": True,
            "valid_for_days": 2,
            "http_status": 302,
        },
        "gateway-error.example": {
            "host": "gateway-error.example",
            "trusted": True,
            "valid_for_days": 90,
            "http_status": 502,
        },
    }

    report = evaluate(tuple(observations), prober=observations.__getitem__)

    assert report["passed"] is False
    assert [item["passed"] for item in report["hosts"]] == [True, False, False, False]
    assert report["mutates_cluster"] is False


def test_preflight_passes_only_when_every_host_is_browser_ready() -> None:
    report = evaluate(
        ("requester.example", "admin.example", "api.example"),
        prober=lambda host: {
            "host": host,
            "trusted": True,
            "valid_for_days": 89,
            "http_status": 302,
        },
    )

    assert report["passed"] is True


def test_probe_reports_resolved_addresses_when_tls_is_not_trusted(monkeypatch) -> None:
    monkeypatch.setattr(
        "preflight_flightpath_tls.socket.getaddrinfo",
        lambda *args, **kwargs: [
            (2, 1, 6, "", ("192.0.2.20", 443)),
            (2, 1, 6, "", ("192.0.2.10", 443)),
            (2, 1, 6, "", ("192.0.2.20", 443)),
        ],
    )

    def reject_connection(*args, **kwargs):
        raise ConnectionRefusedError

    monkeypatch.setattr(
        "preflight_flightpath_tls.socket.create_connection", reject_connection
    )

    result = _probe_host("requester.example")

    assert result["resolved_addresses"] == ["192.0.2.10", "192.0.2.20"]
    assert result["failure"] == "connection-failed"
