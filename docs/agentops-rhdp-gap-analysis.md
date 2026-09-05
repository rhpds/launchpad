# AgentOps RHDP-to-Launchpad gap analysis

This review establishes the deployment contract for the draft
`agentops-observability` catalog item. It separates what the existing RHDP
item actually supplies from what Launchpad must own to offer isolated,
repeatable 5- and 25-seat workshops on Arena.

## Reviewed immutable sources

| Layer | Repository and revision | Purpose |
|---|---|---|
| Catalog orchestration | private `rhpds/agnosticv`, `agd_v2/agentops-intel`, reviewed at `48fc6eebedb295bddf1b915a230e5e90f89db0af` | RHDP variables, workload order, access, and Showroom tabs |
| Launchpad Showroom | `rhpds/launchpad`, `content-agentops-observability`, at `0d697f3ddd1e5008dfd9bb32c3e3bdd0398383a9` | Adapted Antora participant journey |
| Upstream Showroom | `rhpds/agentops-intel-showroom` at `f1881c61de55ebf5640c27e76469f4efe458edaf` | Immutable content and screenshot provenance |
| Launchpad seat chart | `rhpds/launchpad`, `deploy/workloads/agentops-seat`, at `6fc278ec8200802a5dd536a1e76656bd160d697e` | Live-tested namespace-scoped deployment source |
| GitOps automation | `rhpds/agentops-in-prod-automation` at `6ea100531ac869fa66abe69ae223d6b56dbce9a2` | Reviewed RHDP bootstrap provenance; not deployed by Launchpad |
| Application | `rh-ai-quickstart/multi-agent-loan-origination` at `1e50e51c334c1b6ed854d81a3f28fd324792f481` | Mortgage AI application source and base chart |

The GitOps automation, rather than the application chart alone, is the RHDP
workload behavior Launchpad must model. It is not safe to deploy unchanged, so
Launchpad now owns a pinned, namespace-scoped seat chart.

## What RHDP provisions

AgnosticV runs these workloads in order:

1. Keycloak-backed OpenShift authentication and a generated common password;
2. OpenShift GitOps with cluster-admin privileges;
3. a LiteMaaS virtual key for `qwen3-14b`;
4. the AgentOps GitOps bootstrap chart;
5. embedded OpenShift Console support; and
6. Showroom.

The bootstrap creates cluster-global Applications for OpenShift AI, MLflow,
cluster monitoring, logging, and the image puller. It also creates per-user
ApplicationSets for the workspace namespace, Mortgage AI, Grafana, MinIO, and
Data Science Pipelines. The participant namespace is `wksp-user1` in the
current catalog.

The Showroom declares eight tools:

1. OpenShift Console;
2. Terminal;
3. shared MLflow at `https://rh-ai.<ingress>/mlflow/`;
4. Mortgage AI at `https://mortgage-ai-<workspace>.<ingress>`;
5. Grafana at `https://grafana-route-<workspace>.<ingress>`;
6. shared RHOAI at `https://rh-ai.<ingress>/`;
7. MLflow documentation; and
8. RHOAI documentation.

## Why the RHDP bootstrap cannot be reused unchanged

- Global Application and ApplicationSet names collide across concurrent
  orders.
- The catalog explicitly sets `num_users: 1` and
  `workshop_user_mode: single`. A 25-seat Launchpad workshop is new behavior.
- The bootstrap serializes the LiteMaaS virtual key into Argo CD Helm values.
- GitOps and several component charts create cluster-scoped RBAC.
- The RHDP item owns cluster authentication and may remove kubeadmin; Launchpad
  already has a participant identity and namespace entitlement model.
- Its default storage class is ODF/Ceph, while Arena uses `nfs-storage`.
- Its content assumes `qwen3-14b` on Intel Gaudi. Arena is currently a CPU
  execution target with Granite model routes.
- The Showroom points at a mutable `main` content ref and a mutable `latest` UI
  bundle. Launchpad requires immutable revisions.

## Implemented seat foundation

The pinned `deploy/workloads/agentops-seat` chart now renders, per seat:

- Mortgage AI API and UI;
- PostgreSQL and MinIO;
- Grafana;
- Data Science Pipelines;
- a `ServiceMonitor`;
- participant Routes; and
- namespaced service accounts and RBAC.

It renders no `Secret`, `Namespace`, `ClusterRole`, `ClusterRoleBinding`,
`Subscription`, `OperatorGroup`, or `ConsoleLink`. Launchpad creates the runtime
Secret outside GitOps using generated credentials and the seat's LiteMaaS
values. Retry preserves a Launchpad-managed Secret owned by the same session
and refuses to reuse one owned by another session.

Every chart resource carries workshop, seat, session, tenant, and cluster
labels. The Application uses the persisted `cluster_ref`, and its values carry
the same identity. A live Arena server-side dry run accepted all 21 rendered
resources. A later one-seat deployment also proved the operator-generated DSPA
resources.

The RHDP automation was reviewed at its pinned revision after the first live
run. Although the catalog defaults to one user, its ApplicationSets use
`user.count` to create per-user Mortgage AI, MinIO, Grafana, DSPA, and workspace
resources. MLflow, OpenShift AI, monitoring, logging, and the model endpoint are
shared. Launchpad therefore does not need its own AgnosticV/AgnosticD; its
per-seat chart plus shared Arena services matches the relevant RHDP topology.

## Shared topology still required

Install and certify shared Arena prerequisites once, outside an order:

- OpenShift AI and its dashboard;
- user workload monitoring;
- OpenShift Logging/Loki;
- shared MLflow and its namespace authorization model;
- OpenShift GitOps; and
- durable image mirroring or pre-pull policy.

For each workshop, reserve aggregate capacity and persist one Arena assignment.
For each seat, create only uniquely named namespace-scoped resources:

- the participant namespace and `edit` RoleBinding;
- a runtime Secret created directly through the Arena API;
- one namespace-scoped workload Application for Mortgage AI, Grafana, MinIO,
  and DSPA resources;
- one Showroom Application with all eight resolved tabs; and
- ownership labels containing session, workshop, tenant, seat, and cluster IDs.

The adapted charts must accept a pre-existing Secret reference. Argo CD must
never own the virtual key or generated credentials. Reclaim deletes the seat's
Showroom and workload Applications before deleting its namespace, while shared
cluster services remain intact.

## Certification order

1. Confirm shared Arena services and their routes/RBAC.
2. Protect all participant workload and shared-service routes through the
   entitlement gateway.
3. Complete one seat with the adapted Showroom across all eight tabs,
   including traces, metrics, logs,
   pipelines, access isolation, and zero-residue reclaim.
4. Certify five seats with concurrent participant use.
5. Certify 25 seats with staggered provisioning, concurrent participant use,
   model-load measurement, and bulk reclaim.

The catalog remains `draft` until every one-seat requirement is GREEN-live.
The five- and 25-seat limits are promoted only after measured capacity and
repeatability evidence.

## Current Arena prerequisite status

The live read-only inspection completed on 2026-09-04 after the Arena API host
route was corrected to use the VPN interface. Arena is healthy on OpenShift
4.22.3 with five Ready nodes and 1,250 aggregate pod slots. The default
`nfs-storage` class is present. The following AgentOps foundations are already
available:

- OpenShift GitOps 1.21.4;
- OpenShift AI 3.5.0 with a Ready `default-dsc`;
- Data Science Pipelines support;
- a supported shared MLflow 3.14.0 tracking server with workspace-scoped
  authorization (installed and certified on 2026-09-05);
- supported OpenShift Logging and Loki 6.6 operators, a Ready one-seat Loki
  pilot, application-log forwarding limited to `launchpad-*`, and the Console
  logging plugin;
- user workload monitoring; and
- the Launchpad Keycloak route and embedded-console webhook.

The live check and render/dry-run gates established the remaining blockers:

- the shared `rh-ai`/MLflow API and OAuth route are live, but the route's TLS
  chain is not trusted by the external test client and its participant gateway
  journey has not been certified;
- the shared Nomic embedding endpoint and direct AgentOps ingestion are live,
  but they have not yet been exercised through a Launchpad-created seat;
- Arena participant routes present a certificate chain that the external test
  client does not trust;
- OpenShift Logging/Loki passes the one-seat ingestion and namespace-isolation
  check, but its `1x.demo` NFS-backed MinIO topology is not a scale topology;
- direct Mortgage AI and Grafana Routes are not yet protected by the
  participant entitlement gateway; and
- the `launchpad-arena` Argo CD Application is Healthy but OutOfSync at
  `3b5a856dd01a3d30d91bc89e40fadb4267d4cca2`, so its drift must be reviewed
  rather than blindly synchronized.

The two least-privilege Arena service accounts are present. The Launchpad
provisioner can create namespaces and cannot create Applications in the
central GitOps namespace, as intended. The local administrator kubeconfig is
expired and is not a suitable runtime credential; Launchpad must continue to
use its service-account identity.

The remote Argo identity's least-privilege rule was updated on 2026-09-04. It
can create namespaced `ServiceMonitor` and DSPA resources and remains unable to
create cluster roles. This clears the chart's discovered authorization gap but
does not substitute for a real one-seat deployment and functional journey.

The adapted Showroom was added to this repository at
`0d697f3ddd1e5008dfd9bb32c3e3bdd0398383a9`. Its Antora build and source
contract pass with no warnings. It uses Launchpad SSO and the generated seat
namespace, the `granite-3.2-8b-tools` model contract, immutable application and
pipeline references, and chart-aligned Secret, Grafana, and health-check
instructions. The original upstream commit remains recorded in
`content-agentops-observability/UPSTREAM.md`.

## First live seat result

The namespace-scoped chart was deployed on Arena and corrected through explicit
RED/GREEN tests. The live failures found and fixed were an unavailable MinIO
client tag, an NGINX configuration that spawned 172 workers, absent PostgreSQL
runtime roles, an incorrect migration connection boundary, and liveness probes
that killed the API during initialization. The final chart deployment reached
these functional results:

- 12 steady pods were fully Ready and the bootstrap Job completed;
- API and PostgreSQL health returned 200;
- 38 seeded mortgage applications were queryable;
- DSPA reported Ready and Grafana reported a healthy database;
- Granite generation returned 200 in 0.6 seconds;
- a real application WebSocket agent exchange completed in 4.2 seconds and
  persisted checkpoint and audit rows; and
- both participant workload Routes returned 200 when tested with the Arena CA
  bypassed.

The first measured chart footprint was 1.73 CPU, 4,964 MiB memory, 13 pods
including the completed bootstrap Job, and 30 GiB storage. The final integrated
topology with its supported per-seat RHOAI pipeline MariaDB measured 2.08 CPU,
5,720 MiB memory, 14 workload pods including one completed Job, and three PVCs.
Adding one Showroom pod and scheduling margin gives a reservation of 2.5 CPU,
7 GiB, 15 pods, and 30 GiB per seat. A 25-seat order therefore reserves 62.5
CPU, 175 GiB memory, 375 pod slots, and 750 GiB storage before safety headroom.

The initial run was not a completed participant certification. Its missing
embedding and MLflow components were subsequently corrected and re-tested as
described below. The route TLS chain remains untrusted by the external test
client, and all component runs were deployed directly rather than through a
Launchpad Showroom/entitlement order.

## Shared embedding endpoint result

The follow-up Arena component run on 2026-09-05 deployed a private, cached
Text Embeddings Inference service for `nomic-embed-text-v1.5` in
`fleet-llm-d`. The endpoint is registered as a cluster-specific runtime source,
so AgentOps receives its URL in the generated runtime Secret rather than from
catalog literals or Argo CD values. The service has no public Route and admits
only the Launchpad backend and Launchpad-managed namespaces.

The first RED run exposed two integration defects: the namespace default-deny
policy blocked DNS/HTTPS egress, and the newest Nomic Transformers v5 config
was incompatible with the pinned TEI parser. Explicit DNS/HTTPS egress and the
immediately preceding immutable model revision corrected both failures. The
first successful cache fill used 523 MiB and became ready in about 58 seconds.
A restart loaded from the persistent cache and became ready in 40 seconds. A
real `/v1/embeddings` request returned a 768-dimensional vector in 0.288
seconds; the post-restart request completed in 0.164 seconds.

This clears deployment of the shared endpoint itself. `LIVE-AGENTOPS-014`
remains partial until a Launchpad-created AgentOps seat proves that all seeded
knowledge-base chunks are embedded and searchable through the application.

The sanitized live inventory is captured in
`evidence/agentops-arena-prerequisites-2026-09-04.json`; the chart and permission
evidence is captured in `evidence/agentops-seat-overlay-2026-09-04.json`. The
first live workload and reclaim result is captured in
`evidence/agentops-one-seat-live-2026-09-04.json`. The catalog remains draft
until shared services, route authorization, and the complete one-seat journey
are GREEN-live.

The shared embedding component, including the RED/GREEN failures, persistent
cache restart, 25-request burst, and isolation result, is captured in
`evidence/agentops-shared-embedding-live-2026-09-05.json`.

The follow-up seat successfully embedded all 41 seeded chunks at 768
dimensions, returned the expected FHA sections from pgvector semantic search,
and completed a real WebSocket agent request. That run also found that Arena's
general `nfs-storage` class retains PVs and backing directories. AgentOps now
uses the dedicated `launchpad-nfs-ephemeral` StorageClass, whose Delete/no-
archive behavior passed a live PVC, PV, and NFS-directory cleanup probe. The
run and the corrected schedulable-worker capacity boundary are recorded in
`evidence/agentops-embedding-ingestion-live-2026-09-05.json`.

The next integrated component run installed the supported MLflow CR in
`redhat-ods-applications`. MLflow 3.14.0 became Available, accepted a write from
an assigned Launchpad namespace, rejected a cross-workspace write with 403,
and leaked no named experiments through a cross-workspace search. The AgentOps
application recorded one successful seven-span trace while DSPA was Ready,
41/41 embeddings remained present, and a real agent exchange completed. The
final chart topology also reclaimed automatically in 59 seconds with zero
namespace, PV, NFS-directory, or Application residue and no manual repair.

This evidence is still `partial`, not a one-seat release certificate. Shared
MLflow uses SQLite and must move to PostgreSQL before scale; the per-seat RHOAI
pipeline MariaDB connection needs service-ca TLS; and the Launchpad order,
Showroom, runtime Secret, entitlement, participant routes, and Launchpad
reclaim were not run. The exact result is in
`evidence/agentops-mlflow-live-2026-09-05.json`.

The follow-up OpenShift Logging pilot installed the supported Loki, Logging,
and Cluster Observability operators. Its LokiStack, ClusterLogForwarder, and
Console UI plugin report Ready/Available. A participant log marker was returned
from the assigned namespace with HTTP 200, while a cross-namespace query was
denied with HTTP 403. The first broad collector configuration overloaded the
demo stack; limiting collection to `launchpad-*` made ingestion functional.
This is a one-seat result only: before five seats, replace NFS-backed pilot
MinIO and `1x.demo` with durable S3-compatible object storage, suitable dynamic
block storage, and measured production sizing. Evidence is in
`evidence/agentops-logging-live-2026-09-05.json`.

The capacity snapshot is RED for the September 17 exact trio. Arena has 1,250
aggregate pod slots, but only 500 are on the two schedulable workers; the other
750 belong to three `NoSchedule` control-plane nodes. With 193 pods already on
the workers, the three event workshops would require 718 slots before the
required safety margin and 823 with the 20 percent event protection. The
recommended path is two additional 250-pod workers.
Targeted Launchpad scheduling on control-plane nodes remains a pilot-only
alternative that requires explicit risk certification.
