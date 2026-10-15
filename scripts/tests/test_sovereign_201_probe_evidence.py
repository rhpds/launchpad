from pathlib import Path
import subprocess

import pytest


PROBE = Path(__file__).resolve().parents[1] / "certify-sovereign-ai-201-seat.sh"


def test_sovereign_201_probe_verifies_tls():
    source = PROBE.read_text()
    assert "-sSk" not in source
    assert "-sSkL" not in source


def test_sovereign_201_probe_binds_evidence_to_deployed_source_and_images():
    source = PROBE.read_text()
    assert "get applications.argoproj.io -A -o json" in source
    assert ".status.sync.revision" in source
    assert "29e45a00e89f36a7b5180bb5884c541a9694cc0c" in source
    assert "get deployments" in source
    assert "source_revision:$source_revision" in source
    assert "presentation_image:$presentation_image" in source
    assert "adapter_image:$adapter_image" in source


def test_sovereign_201_request_helper_fails_closed_inside_conditionals():
    source = PROBE.read_text()
    assert 'status="$(curl "${args[@]}" "$url")" || return 1' in source
    assert '[[ "$status" == "$expected_status" ]] || return 1' in source
    assert 'jq -e . "$work_dir/body" >/dev/null || return 1' in source


@pytest.mark.parametrize(
    "curl_body",
    [
        "printf '{}' >\"$work_dir/body\"; printf '403'",
        "printf 'not-json' >\"$work_dir/body\"; printf '200'",
        "return 7",
    ],
)
def test_failed_request_cannot_be_accepted_by_retry_condition(tmp_path, curl_body):
    source = PROBE.read_text()
    helper = source.split("request_json() {", 1)[1].split('\nstage=', 1)[0]
    script = (
        'set -euo pipefail\nwork_dir="$1"\n'
        f"curl() {{ {curl_body}; }}\n"
        "request_json() {" + helper
        + '\nif result="$(request_json 200 POST http://example.invalid)"; '
        'then exit 99; fi\n'
    )
    result = subprocess.run(
        ["bash", "-c", script, "probe-test", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
