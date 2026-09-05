# AgentOps RHDP-to-Launchpad gap analysis

This review establishes the deployment contract for the draft
`agentops-observability` catalog item. It separates what the existing RHDP
item actually supplies from what Launchpad must own to offer isolated,
repeatable 5- and 25-seat workshops on Arena.

## Reviewed immutable sources

| Layer | Repository and revision | Purpose |
|---|---|---|
| Catalog orchestration | private `rhpds/agnosticv`, `agd_v2/agentops-intel`, reviewed at `48fc6eebedb295bddf1b915a230e5e90f89db0af` | RHDP variables, workload order, access, and Showroom tabs |
| Showroom | `rhpds/agentops-intel-showroom` at `f1881c61de55ebf5640c27e76469f4efe458edaf` | Antora participant journey |
| Launchpad seat chart | `rhpds/launchpad`, `deploy/workloads/agentops-seat`, at `2fcf40b74387046b657e0050513144afead09892` | Safe namespace-scoped deployment source |
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
the same identity. A live Arena server-side dry run accepted all 21 resources
without creating them.

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
2. Adapt the Showroom to Launchpad identity, URLs, and
   `granite-3.2-8b-tools`, then protect all participant routes.
3. Complete one seat across all eight tabs, including traces, metrics, logs,
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
- a managed MLflow operator and UI deployment;
- user workload monitoring; and
- the Launchpad Keycloak route and embedded-console webhook.

The live check and render/dry-run gates established the remaining blockers:

- there is no shared `rh-ai`/MLflow participant route matching the Showroom
  contract;
- the new per-seat Grafana chart has not yet been live certified;
- OpenShift Logging/Loki is not installed;
- the catalog now selects `granite-3.2-8b-tools`, but the Showroom content still
  documents `qwen3-14b`, `wksp-user1`, and RHDP password authentication; and
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

The sanitized live inventory is captured in
`evidence/agentops-arena-prerequisites-2026-09-04.json`; the chart and permission
evidence is captured in `evidence/agentops-seat-overlay-2026-09-04.json`. The
catalog remains draft until shared services, content adaptation, route
authorization, and the complete one-seat journey are GREEN-live.
