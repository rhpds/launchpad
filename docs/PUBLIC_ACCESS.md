# Public passwordless lab access

Public access is opt-in and release-gated. Existing orders remain internal
when `exposure_policy` is absent. A public order uses one URL and one instructor
code; the code is the sole secret and participant email is only an unverified
identity label.

## Personas

- **Platform operator:** configures `PUBLIC_LABS_DOMAIN`, wildcard DNS/TLS, the
  dedicated public ingress, WAF limits, Keycloak broker secret and OpenShift
  OIDC. Each execution cluster is certified independently.
- **Catalog owner:** verifies the Showroom, workspace, Console, model and
  cleanup journeys before permitting public placement.
- **Instructor:** copies the one-time code, distributes URL/code, monitors
  claimed seats, rotates the code when needed and reclaims the order.
- **Participant:** enters email plus the instructor code. The same normalized
  email can receive multiple active lab entitlements.
- **Release reviewer:** evaluates the evidence manifest, validation matrix and
  100-point rubric. A running pod is not acceptance evidence.

## Fail-closed activation

Production activation requires `PUBLIC_ACCESS_ENABLED=true` and a non-empty
`PUBLIC_LABS_DOMAIN`. The selected cluster must also set
`public_access_enabled: true` and provide public ingress, Console, OAuth and TLS
configuration. Arena is the current execution target; Oberon remains disabled.

For a disposable Arena browser pilot only, `PUBLIC_LABS_SHARED_ORIGIN` can hold
one Cloudflare Quick Tunnel origin and `PUBLIC_ACCESS_PILOT_CLUSTER=arena` can
enable placement without marking the cluster production-certified. The shared
origin supports exactly one active public order. `scripts/start-tunnel.sh` and
`scripts/stop-tunnel.sh` apply and remove those runtime overrides while pinning
every cluster command to the Arena kubeconfig.

Only the entitlement-aware gateway, Keycloak, Console and OAuth routes may use
the public ingress. The normal backend, seat routes, Argo CD, databases, model
endpoints, admin APIs and internal service routes remain private.

## Proof package

- Contract: `contracts/public-access-v1.yaml`
- Behavior: `features/public_lab_access.feature`
- RED/GREEN record: `evidence/public-access/validation-matrix-v5.yaml`
- Component suites: `backend/tests/test_public_access.py` and
  `backend/tests/test_public_tunnel_contract.py`

General availability requires every critical matrix row at `GREEN-live`, a
100/100 rubric, zero high/critical findings, three consecutive 25-seat browser
certifications and zero cleanup residue.
