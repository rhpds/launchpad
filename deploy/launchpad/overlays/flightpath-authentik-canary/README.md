# Flightpath Authentik workforce-access canary

This overlay adds **new** requester and admin routes. It does not replace the
current OpenShift-authenticated routes and does not change participant
Keycloak, lab-code claims, OpenShift Console identity, provisioning, or lab
runtime resources.

Do not apply this overlay until all prerequisites pass:

1. `auth.smg-helix.ai` resolves to a durable Authentik service with trusted TLS.
2. Authentik has one confidential OIDC provider with client ID
   `launchpad-workforce`, issuer slug `launchpad-workforce`, and both exact
   callback URLs from `workforce-proxies.yaml`.
3. The provider emits `preferred_username`, `email`, and a list-valued `groups`
   claim. Group membership is invitation-only.
4. The namespace contains a secret named `launchpad-authentik-workforce` with
   keys `client-id`, `client-secret`, `requester-cookie-secret`, and
   `admin-cookie-secret`. Secrets are generated and stored out of band; no
   plaintext values belong in Git.
5. PostgreSQL backup/restore, Authentik break-glass access, MFA for privileged
   groups, and user-disable behavior have evidence.

The canary routes are:

- `https://launchpad-auth-candidate.apps.flightpath.fm2aihpcsed.com`
- `https://launchpad-admin-auth-candidate.apps.flightpath.fm2aihpcsed.com`

The admin proxy additionally requires `launchpad-admins`. Backend APIs verify
the signed token again and derive tenant access from groups named
`launchpad-tenant:<tenant-id>`.

Render without applying:

```sh
oc kustomize deploy/launchpad/overlays/flightpath-authentik-canary >/tmp/launchpad-authentik-canary.yaml
```

Run the read-only identity preflight before any apply:

```sh
uv run python scripts/preflight_authentik_canary.py \
  --check-cluster-secret \
  --namespace launchpad-flightpath-candidate
```

The report verifies exact issuer/JWKS metadata, HTTPS endpoints, authorization
code flow, S256 PKCE, required scopes, an RS256 signing key, and required
Secret key strength. It never prints credential values.

Promotion is forbidden until the validation matrix in
`docs/authentik-workforce-access.md` is green. This overlay includes the full
Flightpath candidate base, so `oc apply -k` is a **full candidate
reconciliation**, not an identity-only apply. Render and diff it against the
live namespace first. The OIDC values are loaded by the shared backend at
process start, so activation requires a controlled backend rollout. Existing
lab workloads keep running, but requester/admin API traffic can experience a
short control-plane interruption; do not schedule that activation during a
live ordering window.
