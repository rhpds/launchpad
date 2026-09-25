# Flightpath unified identity contract

## Decision

Internal and public lab access use one identity plane and one OpenShift RBAC
contract. Keycloak realm `launchpad-public` issues the stable participant
username, Launchpad persists that username on the order, and OpenShift grants
namespace-scoped access to that exact username.

The login ceremony may differ without changing the identity contract:

- public participant: email plus the order's instructor code;
- internal requester: an authenticated enterprise or managed Keycloak account,
  without an order code;
- automation: API key until a workload-identity migration is complete.

The browser-supplied requester or owner field is never authoritative. For a
trusted OAuth-proxy request, the backend replaces it with
`X-Forwarded-User`. API-key clients retain the existing request contract for
compatibility.

## Required request path

1. The requester signs in before opening the order form.
2. `GET /api/v1/auth/me` returns the trusted identity summary.
3. The UI displays the identity as read-only.
4. The backend binds an individual request or workshop owner to the same
   identity, regardless of the submitted JSON value.
5. Provisioning creates `RoleBinding/launchpad-participant` only for that
   persisted identity.
6. OpenShift maps Keycloak `preferred_username` to the same OpenShift user.
7. Reclaim or expiry removes the namespace and its RoleBinding.

## Flightpath activation gates

Do not add the cluster-wide OpenShift identity provider until all gates pass:

| Gate | Required evidence |
|---|---|
| Keycloak issuer | Trusted TLS and exact issuer `https://labs.smg-helix.ai/realms/launchpad-public` |
| Internal login source | Enterprise broker or managed internal account flow tested without an order code |
| Client separation | OpenShift OIDC client uses the internal browser flow; the public gateway retains the order-code flow |
| Console TLS | The Flightpath Console hostname is browser-trusted on the intended network |
| Mapping | `preferred_username` is stable and matches the persisted Launchpad requester |
| Isolation | Own namespace edit succeeds; other namespaces and nodes are denied |
| Recovery | Existing `kubeadmin` fallback remains usable during the canary |
| Health | Authentication and Console operators remain Available and not Degraded |

The identity provider must be merged into the existing `OAuth/cluster`
provider list. It must never replace the full list. Activation begins with one
new internal individual lab, then one workshop owner, before it is enabled for
general ordering.

## Workshop boundary

An internal workshop order authenticates the owner at creation time. It does
not yet identify all participants. Participant identities must be collected by
the same entitlement/claim mechanism used for public workshops, or by an
enterprise roster import, before per-seat Console access can be considered
complete.
