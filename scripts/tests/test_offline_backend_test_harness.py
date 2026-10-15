"""Mock regressions must not use inherited live telemetry endpoints."""

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def test_backend_harness_clears_external_telemetry_before_application_import():
    environment = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "backend"),
        "KAFKA_BOOTSTRAP_SERVERS": "not-a-test-broker.invalid:9092",
        "STARGATE_API_URL": "https://not-a-test-stargate.invalid",
        "DASHBOARD_AUDIT_URL": "https://not-a-test-dashboard.invalid",
    }
    result = subprocess.run(
        [sys.executable, "-c", (
            "import runpy; runpy.run_path('backend/tests/conftest.py'); "
            "from app.integrations import kafka_publisher, event_publisher; "
            "assert not kafka_publisher.KAFKA_BOOTSTRAP; "
            "assert not event_publisher.STARGATE_API_URL; "
            "assert not event_publisher.DASHBOARD_AUDIT_URL"
        )],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
