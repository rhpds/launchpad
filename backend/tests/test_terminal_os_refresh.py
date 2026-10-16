from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_terminal_refreshes_os_without_removing_learner_tools():
    source = (ROOT / 'workshop-images/showroom-terminal/Containerfile').read_text()
    assert 'FROM quay.io/rhpds/openshift-showroom-terminal-ocp@sha256:606317dc396db33b879c1d3807844990cd37bb0c787b0b525edbeb70283b5350' in source
    assert 'dnf -y --refresh upgrade' in source
    assert 'dnf clean all' in source
    assert 'dnf remove' not in source
    assert '|| true' not in source
    assert source.index('USER 0') < source.index('dnf -y --refresh upgrade') < source.index('USER 1001')
    assert 'ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/launchpad-runttyd"]' in source


def test_terminal_os_refresh_restores_runtime_user_after_upgrade():
    # The el10 package upgrade drops the base image's hand-added uid 1001
    # entry from /etc/passwd, which breaks every learner CLI that performs a
    # user lookup (odo exits with "user: unknown userid 1001"). The image must
    # restore the exact inherited entry so the platform's arbitrary-uid
    # runtime contract keeps working.
    source = (ROOT / 'workshop-images/showroom-terminal/Containerfile').read_text()
    assert "grep -q '^1001:' /etc/passwd" in source
    assert "1001:*:1001:0:container user:/home/lab-user:/bin/sh" in source
    assert (
        source.index('dnf clean all')
        < source.index("grep -q '^1001:' /etc/passwd")
        < source.index('USER 1001')
    )
