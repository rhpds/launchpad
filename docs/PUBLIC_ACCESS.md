# Public passwordless lab access

Public access is opt-in and release-gated. Existing orders remain internal
when `exposure_policy` is absent. A public order uses one URL and one instructor
code; the code is the sole secret and participant email is only an unverified
identity label.

## Personas

- **Platform operator:** configures `PUBLIC_LABS_DOMAIN`, the approved DNS/TLS
  ingress mode, WAF limits, Keycloak broker secret and OpenShift OIDC. Each
  execution cluster is certified independently.
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

## Production ingress when wildcard DNS is prohibited

Intel's external-ingress policy does not permit wildcard DNS and permits only
HTTPS inbound traffic. That policy rules out the current per-order hostname
shape (`https://<catalog>-<order>.<PUBLIC_LABS_DOMAIN>`), but it does not rule
out public Launchpad access.

Use one of these mutually exclusive production patterns:

1. **Named Cloudflare Tunnel (preferred when outbound tunnel traffic is
   approved):** Intel creates one exact `labs.fm2aihpcsed.com` CNAME for a
   permanent, account-managed tunnel. Arena needs no public IP or inbound NAT.
   The firewall must permit `cloudflared` egress on TCP or UDP 7844; HTTPS-only
   browser traffic is unchanged. The hostname (or a delegated DNS zone
   containing it) must be managed in the same Cloudflare account as the
   tunnel; otherwise use the static-IP pattern. Quick Tunnels remain test-only.
2. **Static IP with HTTPS-only NAT:** Intel creates one exact
   `labs.fm2aihpcsed.com` A record and forwards TCP 443 to an isolated Arena
   ingress/gateway. TCP 80 is optional and is not a prerequisite. Certificate
   issuance must use DNS-01 or an Intel-provided public certificate because an
   HTTP-01 challenge cannot depend on port 80.

Both patterns require a single-origin URL contract such as
`https://labs.fm2aihpcsed.com/labs/<catalog>-<order>`. The entitlement gateway
must route order paths to private seat services and preserve WebSocket traffic.
Keycloak/OIDC callback URLs must use the same stable origin. Native OpenShift
Console exposure either needs separately approved exact Console and OAuth
hostnames or must remain behind the same tested gateway; dynamic seat Routes
must never be published individually.

Before implementing this mode, version the public-access contract and add RED
tests for path isolation, callback generation, multi-order routing, WebSockets,
cross-order denial, rotation, expiration and cleanup. Do not set a production
cluster's `public_access_enabled` flag from DNS approval alone.

Cloudflare references: [Tunnel DNS records](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/dns/),
[locally managed ingress rules](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/configuration-file/),
[Tunnel firewall requirements](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-with-firewall/),
and [Quick Tunnel limitations](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/).

## Proof package

- Contract: `contracts/public-access-v1.yaml`
- Behavior: `features/public_lab_access.feature`
- RED/GREEN record: `evidence/public-access/validation-matrix-v5.yaml`
- Component suites: `backend/tests/test_public_access.py` and
  `backend/tests/test_public_tunnel_contract.py`

General availability requires every critical matrix row at `GREEN-live`, a
100/100 rubric, zero high/critical findings, three consecutive 25-seat browser
certifications and zero cleanup residue.
