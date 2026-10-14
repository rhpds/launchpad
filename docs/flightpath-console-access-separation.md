# Flightpath Console and participant access separation

Status: Proposed; preparation approved, live cutover not approved or performed.
Date: 2026-10-14.
Decision owners: Launchpad owner and Flightpath/network owner.

## Update: native-route option worth testing before new DNS

October 14 local tests confirm the existing tunnel code can translate public
Console authorization to a native operator-managed callback, rewrite native
Console responses back to the public participant origin, and keep participant
root versus namespace Console dispatch separate. This is a counterfactual
configuration test, not a live route or browser certification.

Therefore the separate Console hostname below is an option, not a proven
infrastructure requirement. Before asking for more DNS, evaluate restoring the
native Console hostname while configuring the tunnel's Console upstream Host
and accepted callback to that native hostname. Keep the labs hostname, Keycloak
issuer, existing participant links, namespace RBAC, and participant-only proxy
IDP selection unchanged.

Live prerequisites include reviewing both Console and ingress component-route
settings, capturing a rollback snapshot, approving a change window, and testing
native kubeadmin login plus one complete embedded participant Console journey.
Do not remove the live custom route or change the tunnel environment from the
local tests alone. Native browser certificate trust remains a separate issue.

Scoped evidence:
`evidence/runs/flightpath-native-console-counterfactual-green-scoped-20261014.xml`.
The broader attempt is preserved as
`evidence/runs/flightpath-native-console-counterfactual-attempt-r1-20261014.xml`:
one legacy Arena overlay render fails on its existing NetworkPolicy patch. It
is excluded from the scoped Flightpath/router result, not declared passing.

## Outcome

Ordinary Flightpath cluster access must reach OpenShift authentication, not
Launchpad's participant email/code form. Participant Console access must remain
bound to the assigned lab identity and namespace. Do not share administrative
credentials through a catalog, Showroom, or participant portal.

## Verified current behavior

Read-only checks on October 14 found:

- The native Console root returns HTTP 301 to `https://labs.smg-helix.ai/`.
- `console.operator.openshift.io/cluster.spec.route.hostname` is
  `labs.smg-helix.ai`, with Secret reference `launchpad-public-console-tls`.
- The native `openshift-console/console` Route targets `console-redirect`.
- `openshift-console/console-custom` targets `console` at the labs hostname.
- The operator-managed Console OAuthClient accepts
  `https://labs.smg-helix.ai/auth/callback`.
- The authoritative cluster Console URL is `https://labs.smg-helix.ai`.
- Saved tunnel code automatically adds `idp=launchpad-public` to Console OAuth
  authorization requests when no provider is specified. The live router code
  has not yet been independently compared byte-for-byte with this source.
- `/console/` returns a redirect to `/`; it is not a verified staff workaround.

The shared canonical hostname explains the immediate redirect independently of
email, instructor code, Authentik, or browser session state.

## Proposed boundary

Reserve `labs.smg-helix.ai` for Launchpad participant access and existing lab
URLs. Request the distinct hostname `console-flightpath.smg-helix.ai` for
OpenShift Console, subject to infrastructure approval. This hostname is a
proposal, not an existing or verified endpoint.

Staff use the Console host and normal approved OpenShift identity providers.
Lab participants reach Console from their lab with explicit participant IDP
selection and existing namespace RBAC. Different hostnames do not themselves
provide authorization or guarantee iframe SSO.

Keep requester/admin Authentik onboarding separate. This repair must not enable
that unfinished canary or change its workforce role mapping.

## Infrastructure ask and ownership

Ask Caiti/the Cloudflare zone owner to approve the Console hostname and choose
one of these access policies before routing it:

1. Private/VPN-only staff access, with a separately approved path for embedded
   participant Console; or
2. A publicly reachable Console login through the named tunnel, explicitly
   approved for both staff and namespace-scoped participants.

A public Console hostname exposes the login surface. It does not grant a
cluster role, but it is not merely a training-dashboard DNS change. Do not
enable this exposure without owner approval. Cloudflare Access, if required,
must be tested for participant compatibility rather than silently added.

For an approved public Console hostname, request an exact-host DNS record
attached to the existing Flightpath named tunnel, with Cloudflare edge HTTPS.
No wildcard record, new public IP, port 80, or public Kubernetes API is needed
for this proposal. Route to a specifically configured Console dispatch path;
do not use a catch-all to the Launchpad gateway.

Confirm who delivers a hostname-valid origin certificate and full chain via a
Secret, or which approved encrypted origin path replaces that requirement.
Cloudflare's browser-facing certificate does not establish trust between
cloudflared, the router, and the OpenShift origin. Do not accept disabled origin
verification as the final certificate solution. Never put keys or tunnel tokens
in Git, email, or lab instructions.

Caiti/zone owner owns DNS, tunnel-host approval, edge policy, and certificate
delivery. Launchpad owner owns router dispatch, application/callback changes,
participant integration, evidence, and coordinated rollback.

## Implementation sequence — gated, not executed

1. Capture a restricted rollback snapshot of Console settings, Routes,
   OAuthClient callbacks, tunnel configuration, Keycloak redirects, and
   participant access configuration. Do not export Secret values to Git.
2. Inventory active orders and compare deployed router code with saved source.
   Approve a window; a canonical Console change may interrupt browser sessions.
3. Build and test exact-host dispatch. Console root/assets/API/auth routes on
   the Console host must reach Console, never the participant gateway.
   Unknown hosts must fail closed. Preserve all existing labs-host routes.
4. Remove unconditional participant IDP selection from the staff flow. Select
   `launchpad-public` only through an explicit participant journey; provider
   selection is not a substitute for namespace RBAC.
5. Install approved DNS/TLS and update the operator-owned Console hostname and
   corresponding callback configuration together. Do not scale down the
   Console operator to preserve manual OAuthClient edits.
6. Update participant Console link generation, redirect translation, accepted
   origins, iframe policy, and session handling for the separate host. Verify
   Keycloak SSO and modern browser cookie restrictions; do not assume cookies
   can simply be shared between origins.
7. Certify one disposable seat before publishing new links. Then update the
   protected cluster-access handoff page without including its capability URL
   or credentials in this repository.

If separate-origin embedded Console cannot pass browser security/SSO gates,
stop before cutover and review a separately configured participant Console
instance. Do not force a new-tab fallback or change namespace permissions
without approval.

## Required proof

Write failing regressions first for the current mixed-root routing and forced
staff participant-IDP behavior. Require local GREEN before live changes.

- Contract/component: staff root selects Console; labs root selects Launchpad;
  unknown hosts denied; callback URLs agree; explicit participant IDP preserved.
- Staff browser: native Console link reaches the intended Console; normal
  provider login, return navigation, refresh, and logout work without a code.
- Participant browser: email/code claim, embedded Console, refresh, and logout
  work; no recursive frames, popups, or administrative credential prompts.
- Authorization: participant may edit only its assigned namespace; other-seat,
  other-tenant, node, and cluster-admin checks are denied.
- TLS: default-trust browser HTTPS and approved verified origin transport.
- Lifecycle: expiry/rotation deny access; reclaim removes entitlement and
  RoleBindings; the disposable certification order leaves zero residue.
- Compatibility: Showroom, Terminal, workspaces, requester/admin, and an
  existing lab journey remain functional.

Record the candidate commit/image, approved hosts, redirect results, browser
evidence, authorization results, and cleanup receipt. Do not mark this change
GREEN-live from HTTP headers or pod readiness alone.

## Rollback

Stop on failed staff login, changed participant identity, broader permissions,
broken embedded Console, callback mismatch, or lab-route regression. Restore
the captured hostname/callback/router/participant configuration as a coordinated
set, not just one Route. Preserve database records and running lab namespaces.
No cluster restart, drain, or lab reprovision is part of this proposal.

## Alternatives

Changing only the handoff link does not repair the canonical Console redirect.
Removing the custom hostname alone risks breaking participant callbacks.
Keeping the shared hostname with special staff paths perpetuates routing and
cookie ambiguity. A second Console instance offers separation without changing
the existing canonical instance, but adds operational and certification burden;
it is the fallback decision, not an approved deployment.
