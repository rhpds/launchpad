from pathlib import Path


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
