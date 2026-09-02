from pathlib import Path


def test_passwordless_authenticator_populates_required_profile_fields():
    source = (
        Path(__file__).resolve().parents[2]
        / "keycloak-authenticator/src/main/java/com/redhat/launchpad/LaunchpadCodeAuthenticator.java"
    ).read_text()

    assert 'user.setFirstName("Launchpad")' in source
    assert 'user.setLastName("Participant")' in source


def test_login_brand_assets_have_cache_busting_versions():
    template = (
        Path(__file__).resolve().parents[2]
        / "keycloak-authenticator/src/main/resources/theme-resources/templates/launchpad-code.ftl"
    ).read_text()
    assert "redhat.svg?v=" in template
    assert "intel.svg?v=" in template
