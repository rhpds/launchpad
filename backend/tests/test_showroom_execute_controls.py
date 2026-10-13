from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_execute_finds_terminal_by_its_contract_not_legacy_tab_classes():
    bridge = (ROOT / "content/supplemental-ui/js/vendor/clipboard.js").read_text()
    assert 'iframe[src*="/terminal"]' in bridge
    assert 'getAttribute("role")' in bridge
    assert ".tabcontent.active" not in bridge
    assert "inputType: 'insertText'" in bridge
    assert "key: 'Enter'" in bridge


def test_instruction_header_uses_both_approved_partnership_assets():
    header = (ROOT / "content/supplemental-ui/partials/header-content.hbs").read_text()
    assert "redhat-logo.svg" in header and "intel-logo.svg" in header
    assert "Demo Platform" not in header
