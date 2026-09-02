from pathlib import Path


def test_passwordless_authenticator_populates_required_profile_fields():
    source = (
        Path(__file__).resolve().parents[2]
        / "keycloak-authenticator/src/main/java/com/redhat/launchpad/LaunchpadCodeAuthenticator.java"
    ).read_text()

    assert 'user.setFirstName("Launchpad")' in source
    assert 'user.setLastName("Participant")' in source


def test_unverified_email_is_a_label_not_a_keycloak_unique_identifier():
    source = (
        Path(__file__).resolve().parents[2]
        / "keycloak-authenticator/src/main/java/com/redhat/launchpad/LaunchpadCodeAuthenticator.java"
    ).read_text()
    assert 'user.setEmail(username + "@participants.invalid")' in source
    assert 'user.setSingleAttribute("launchpad_email_label", email.strip().toLowerCase())' in source
    assert "user.setEmail(email.strip().toLowerCase())" not in source


def test_login_brand_marks_are_inline_and_do_not_depend_on_external_images():
    template = (
        Path(__file__).resolve().parents[2]
        / "keycloak-authenticator/src/main/resources/theme-resources/templates/launchpad-code.ftl"
    ).read_text()
    assert '<svg class="launchpad-logo launchpad-logo-redhat"' in template
    assert '<svg class="launchpad-logo launchpad-logo-intel"' in template
    assert 'viewBox="0 0 192.3 146"' in template
    assert '>Red</text>' not in template
    assert "redhat.svg" not in template
    assert "intel.svg" not in template
    assert 'font-family: "Red Hat Text"' in template
    assert "radial-gradient" in template
    assert "keycloak-bg-darken.svg" not in template
