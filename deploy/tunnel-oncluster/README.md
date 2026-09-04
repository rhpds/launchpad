# Arena public-access pilot tunnel

This deployment provides a disposable, single-host Cloudflare Quick Tunnel for
manual public-access certification on Arena. It is not production ingress.

The router keeps the participant gateway, Keycloak, OpenShift OAuth, Console,
Showroom, and terminal reachable through one temporary origin. OpenShift's
native OAuth callback remains unchanged; only browser-visible, plain-text route
locations are rewritten. Encoded `redirect_uri` values are intentionally left
alone so the Console's operator-managed OAuth client remains authoritative.

## Safety boundary

- Every cluster command is pinned to `/Users/jkershaw/.kube/config-arena`.
- The tunnel has a dedicated ServiceAccount with no Kubernetes API token or
  RBAC permissions.
- The Console operator, `OAuthClient/console`, and `OAuth/cluster` are never
  patched by this deployment.
- The gateway validates the stable Arena Keycloak issuer. Split browser and
  back-channel endpoints do not disable token issuer verification.
- A new pilot order receives the shared tunnel origin from the backend. An
  existing order is moved through an authenticated, audited Launchpad API;
  PostgreSQL is not edited directly.
- Starting a tunnel never changes the instructor code.

## Start

The backend and Keycloak authenticator images containing the current commit
must be deployed first. Start the tunnel before creating a new public order:

```sh
./scripts/start-tunnel.sh
```

The command refuses any cluster other than Arena, verifies that the Console
operator is running and the `launchpad-public` identity provider uses Arena's
stable Keycloak issuer, enables public placement only on Arena, then prints the
temporary public URL. Create one public individual lab or workshop through the
requester portal and use the one-time instructor code returned with the order.

To reuse an already-created public order without changing its code, pass its ID:

```sh
./scripts/start-tunnel.sh <public-order-id>
```

## Stop

```sh
./scripts/stop-tunnel.sh
```

Stopping disables the Arena pilot placement override, removes the shared
origin, scales down the public gateway and tunnel, and restores the checked-in
`PUBLIC_ACCESS_ENABLED=false` setting. It does not modify OpenShift
authentication or Console operators.

## Production boundary

Quick Tunnel hostnames change after a restart. Because every pilot order shares
one hostname, only one active public order may be tested at a time. Production
requires owned DNS, trusted TLS, a stable named tunnel or public ingress,
explicit public-route isolation, and a fresh external certification run.
