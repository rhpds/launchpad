from pathlib import Path


def test_passwordless_authenticator_populates_required_profile_fields():
    source = (
        Path(__file__).resolve().parents[2]
        / "keycloak-authenticator/src/main/java/com/redhat/launchpad/LaunchpadCodeAuthenticator.java"
    ).read_text()

    assert 'user.setFirstName("Launchpad")' in source
    assert 'user.setLastName("Participant")' in source


def test_login_brand_marks_are_inline_and_do_not_depend_on_external_images():
    template = (
        Path(__file__).resolve().parents[2]
        / "keycloak-authenticator/src/main/resources/theme-resources/templates/launchpad-code.ftl"
    ).read_text()
    assert 'class="launchpad-brand-mark launchpad-brand-mark-redhat"' in template
    assert 'class="launchpad-brand-mark launchpad-brand-mark-intel"' in template
    assert "${url.resourcesPath}/img/" not in template
