# September 17 three-workshop readiness gate

## Event outcome

On **September 17, 2026**, the Launchpad execution fleet must support these
three separate workshop orders. Provisioning remains staggered, but all 75
participant seats must remain usable concurrently:

| Provision order | Catalog item | Participant seats | Current release state | Candidate target |
|---|---|---:|---|---|
| 1 | `agentops-observability` | 25 | GREEN-live-5 internal; 25-seat gate remains RED | Arena after topology reduction or qualified capacity expansion |
| 2 | `intel-llm-cpu-serving` | 25 | GREEN-live-25 on Arena | Oberon after re-certification |
| 3 | `intel-xeon6-agent-201` | 25 | GREEN-live-25 internal on Brutus | Brutus, placement-disabled pending event go/no-go |

Provisioning is deliberately staggered. Request the next workshop only after
the previous workshop is collectively Ready, but retain all three so 75
participants can use their seats concurrently. This is not a requirement to
create all 75 seats at the same instant.

The event provisioning order is **AgentOps first**, Serve LLMs second, and
Building an AI Agent third. AgentOps has the largest footprint and the longest
initialization path, so it must fail early enough to preserve recovery time.
The candidate targets above are a remediation plan, not certified placement.

## What is already proven

Arena has already passed the platform-level pattern needed for this event.
`evidence/arena-staggered-three-workshops-2026-09-04.json` records three
different 25-seat workshops provisioned one at a time, held together, exercised
by 75 concurrent participant journeys, and reclaimed with zero residue. The
run included the exact Serve LLMs and Building an AI Agent catalog items.

That evidence does not include AgentOps. Its third workshop was LLM Tool
Calling. AgentOps now has separate GREEN-live five-seat evidence, but neither
proof certifies 25 AgentOps seats, public access, or the proposed Brutus/Oberon
placement. Therefore the previous run proves the Launchpad orchestration
pattern, not the September 17 release candidate.

## Declared capacity envelope

The reservation below comes from the catalog contracts and the measured
AgentOps one-seat footprint. It excludes shared model and Launchpad control
plane services that are already running.

| Workshop | CPU | Memory | Pod slots | Declared seat storage |
|---|---:|---:|---:|---:|
| AgentOps, 25 seats | 62,500m | 179,200 MiB | 425 | 750 GiB |
| Serve LLMs, 25 seats | 16,625m | 37,200 MiB | 50 | not declared by catalog |
| Building an AI Agent, 25 seats | 10,375m | 22,800 MiB | 75 | not declared by catalog |
| **Event total** | **89,500m** | **239,200 MiB** | **550** | **at least 750 GiB** |

Admission must retain at least 20 percent additional headroom for scheduling,
operator activity, model services, temporary rollout overlap, and measurement
error. The protected target is therefore 107,400m CPU, 287,040 MiB memory, 660
pod slots, and at least 900 GiB schedulable storage.

These are reservations, not a statement of current availability. **The current
free Arena capacity must be measured live** immediately before each
certification run and again before the event. Admission must use requested
resources and per-node schedulability, not aggregate allocatable capacity
alone. NFS free space, PVC binding latency, and I/O under 25 AgentOps seats are
explicit gates.

### Live Arena decision — September 5

The first aggregate inventory appeared to show 1,250 pod slots, but three of
the five nodes are control-plane nodes with a `NoSchedule` taint. Only `gnr2`
and `rhgnr1` are schedulable workers:

| Worker measurement | Live value |
|---|---:|
| Schedulable worker nodes | 2 |
| Schedulable pod slots | 500 |
| Running pods on workers | 218 |
| AgentOps-qualified workers | 1 (`gnr2`) |
| Running pods on the qualified worker | 41 |
| Unrequested worker CPU | 336,989m |
| Unrequested worker memory | 1,281,934 MiB |
| NFS free space reported | 6.5 TiB |

CPU, memory, and NFS are not the immediate constraint. Pod slots and qualified
worker topology are. Twenty-five AgentOps seats reserve 425 pod slots. The only
qualified worker has 250 slots and 41 active pods; retaining the standard 20
percent node reserve leaves 159 additional slots, a 266-slot shortage. Even if
the currently unstable `rhgnr1` were relabeled without remediation, the two
workers together have only 182 additional protected slots at the current
218-pod baseline. The measured path is a shared-service topology reduction or
**two additional qualified 250-pod workers**; one new worker still would not
retain the required headroom at the current baseline.

Arena's zero-replica worker MachineSet has no available BareMetalHost behind
it. All registered BareMetalHosts are unmanaged control-plane hosts, so Intel
must attach/register worker hardware before a MachineSet scale operation can
produce nodes. Neither Oberon nor Brutus is a fallback for this workshop:
neither has the full AgentOps capability set or a qualified worker, and their
current protected pod availability is 37 and 91 respectively.

A pilot-only alternative is to add targeted tolerations to Launchpad workloads
so selected participant pods can use the three otherwise idle control-plane
nodes. That supplies enough aggregate slots but creates control-plane
availability risk and needs its own load, eviction, API-latency, rollback, and
failure certification. It must not be enabled as an incidental chart change.

Scaling down unrelated deployments cannot solve this constraint: even an
otherwise empty two-worker pool cannot retain headroom around all 550 declared event pods.
Running the workshops sequentially also does not meet the
requirement because all 75 participants must use the labs concurrently.

### Live fleet decision — September 5 after the AgentOps five-seat run

The build-83 RED run exposed two independent defects: seats concentrated on
unstable `rhgnr1`, and a queued seat could begin after workshop reclaim. Bounded
cleanup removed the run namespaces, but one protected PostgreSQL PV remains
quarantined because its backing NFS files belong to the deleted namespace UID.
It requires an approved storage-administrator procedure and is not hidden by
later evidence. See
`evidence/agentops-five-seat-red-live-build83-2026-09-05.json`.

Build 84 then passed the internal five-seat release gate at 100/100. All five
seats became Ready on qualified `gnr2` in bounded two-seat waves: 65/65 steady
pods were Ready with zero restarts, 55/55 guide pages returned 200, all five
namespace and cross-seat authorization checks passed, all five knowledge bases
held 41 embedded chunks, and five simultaneous grounded agent journeys
completed at 40.669-second p95. Normal bulk reclaim completed in 106 seconds
with zero run-specific namespaces, Applications, or PVs. A separate reclaim
during provisioning created only two sessions, canceled the other three queued
seats, and completed in 171.517 seconds with the same zero-residue result. See
`evidence/agentops-five-seat-functional-live-build84-2026-09-05.json`.

Current pod-slot snapshots and the standard 20 percent reserve produce this
candidate fleet assignment:

| Cluster | Schedulable pod slots | Active worker pods | Additional slots after reserve | Candidate event role |
|---|---:|---:|---:|---|
| Arena | 500 | 218 | 182 | AgentOps; five seats certified, 25 blocked on qualified capacity/topology |
| Brutus | 250 | 109 | 91 | Building an AI Agent; 75-pod contract passed the internal 25-seat gate |
| Oberon | 500 | 363 | 37 | Serve LLMs; currently thirteen slots short of its 50-slot peak contract |

Brutus and Oberon are now registered with separate least-privilege Launchpad
and Argo credentials but remain disabled for normal placement. Brutus's compact
Agent 201 topology uses three pods per seat by co-locating the tools process
with the agent while preserving separate services and routes. It passed one,
five, and 25 internal seats on September 5. The 25-seat workshop reached Ready
in 168 seconds, deployed 75 pods/150 containers with zero restarts, completed
25 simultaneous three-tool journeys with a 79.45-second p95, retained 16 pod
slots below the protected ceiling, and reclaimed to the exact 109-pod baseline
with zero namespaces, PVs, or Applications. A final one-seat regression rendered
the corrected immutable v1.0.13 guide and completed the functional journey.
The retained 100Gi registry stayed healthy throughout. Evidence is in
`evidence/brutus-agent-201-three-pod-certification-2026-09-05.json`.

This passes Brutus's internal 25-seat scale gate, but does not certify public
access, Console OIDC, a 60-minute soak, or three consecutive scale runs. Brutus
therefore remains disabled pending an explicit event go/no-go. Oberon is also
disabled and must be re-certified before it hosts event seats. The preferred
three-cluster path is now:

1. Keep Arena dedicated to AgentOps and reduce the per-seat topology by moving
   DSPA, pipeline database, MinIO, Grafana, and other safe components to one
   workshop-scoped shared stack, or add stable worker capacity.
2. Hold Brutus at the proven three-pod contract, complete the 60-minute soak
   and two repeat 25-seat runs, then decide whether internal event placement
   can be enabled. Keep public access and Console OIDC as separate gates.
3. Re-enable Oberon only after removing at least eleven baseline pod slots and
   passing Serve LLMs 1 -> 5 -> 25 plus full reclaim.

The AgentOps catalog may now expose up to five internal seats. Do not raise it
above five or enable uncertified targets until the next measurements are
GREEN-live. Placement must include per-node pod, CPU, memory, taint, topology,
qualification labels, and recent Ready-transition checks; aggregate cluster
totals are insufficient.

## Critical path: AgentOps 1 -> 5 -> 25

Building an AI Agent now has target-specific internal 25-seat evidence on
Brutus. Serve LLMs still needs target-specific Oberon re-certification. The
release critical path is AgentOps 1 -> 5 -> 25 plus Oberon Serve LLMs and the
exact fleet rehearsal; no result may be promoted from another cluster.

### Gate A: one Launchpad-created AgentOps seat

- Create the order through Launchpad on Arena, including its persisted session,
  workload Application, runtime Secret, Showroom, and entitlement.
- Prove all 41 seeded knowledge-base chunks receive 768-dimensional vectors
  from the private shared Nomic endpoint and can be retrieved semantically.
- Complete the participant journey across Mortgage AI, Grafana, MLflow,
  OpenShift AI, Data Science Pipelines, metrics, logs, and the namespace-scoped
  terminal/Console experience.
- Prove participant workload and shared-service routes through the entitlement
  gateway, including cross-seat and cross-tenant denial.
- Reclaim through Launchpad and prove zero namespace, Route, RoleBinding,
  Application, Secret, entitlement, or model-key residue.

The September 5 integrated component rerun cleared the embedding, shared
MLflow, DSPA, application, trace, and automatic-cleanup sub-gates. All 41
chunks were embedded at 768 dimensions, the WebSocket agent completed, DSPA
reported Ready, and MLflow 3.14.0 recorded one isolated seven-span trace.
Assigned-workspace MLflow writes returned 200, cross-workspace writes returned
403, and no named experiments leaked through cross-workspace search. The final
chart topology reclaimed its namespace, PVs, and NFS directories in 59 seconds
without manual repair.

The OpenShift Logging sub-gate subsequently passed at one-seat pilot scale: the
supported 6.6 operators, LokiStack, forwarder, and Console plugin are live; an
assigned participant queried its marker with HTTP 200 and received HTTP 403
for a cross-namespace query.

The internal form of Gate A passed on September 5 through one Launchpad-created
order. The order created the runtime Secret, workload and Showroom Applications,
exact participant namespace, operator-aware readiness gate, complete AI and
observability journey, and automatic zero-residue reclaim. The model key was
absent from Argo CD and cleared from the reclaimed session. Evidence is in
`evidence/agentops-launchpad-one-seat-2026-09-05.json`.

Public-code access and trusted external TLS remain RED and are not implied by
the internal Gate A result. Shared MLflow metadata moved to persistent
PostgreSQL with verified OpenShift service-ca TLS on September 5. A second
clean Launchpad order also proved that the per-seat pipeline MariaDB rejects
plaintext, accepts hostname-verified service-ca TLS 1.3, creates all pipeline
tables, reaches current-generation DSPA Ready, stays Argo Synced/Healthy after
CA injection, and reclaims with zero residue in 66 seconds.

That proof uses a documented RHOAI 3.5 compatibility boundary: `podToPodTLS`
is disabled because the operator-generated MLMD server TLS configuration drops
the database TLS options. The external MLMD route is disabled and NetworkPolicy
limits database ingress, but an upstream-supported encrypted configuration for
every internal pipeline hop is still required before production. Before production activation,
the `1x.demo` NFS/MinIO logging topology remains a pilot boundary. Arena has
only two storage-capable workers; a supported internal ODF deployment requires
three. The controlled five-seat certification can retain the pilot while it
measures ingestion, query latency, restarts, and storage growth, but production
activation still requires durable S3-compatible object storage, dynamic block
storage, and production sizing. Evidence is in
`evidence/agentops-mlflow-postgres-live-2026-09-05.json` and
`evidence/agentops-pipeline-database-tls-live-2026-09-05.json`.

### Gate B: five AgentOps seats

GREEN-live on build 84. One five-seat workshop achieved 5/5 collective
readiness, isolated terminals/databases/traces, five simultaneous grounded
agent journeys, and zero-residue reclaim. The interrupted-provisioning scenario
also proved queued seats cannot start after reclaim. The catalog is capped at
five internal seats. Public access and the 25-seat boundary remain separate
gates.

### Gate C: 25 AgentOps seats

- Revalidate Arena capacity, reserve the whole workshop atomically, and reject
  the order before creating seats if the protected envelope cannot fit.
- Require 25/25 seats Ready and 25 simultaneous complete participant journeys.
- Hold the workshop for at least 60 minutes while watching node pressure, NFS,
  shared model/embedding latency, DSPA reconciliation, and route stability.
- Reclaim all seats and require zero residue.

### Gate D: exact September fleet trio

- Provision AgentOps 25 on its certified target, wait for collective Ready,
  then provision Serve LLMs 25 on its certified target, wait for Ready, then
  provision Building an AI Agent 25 on its certified target.
- Keep all 75 seats active and validate all 75 participant journeys in one
  bounded concurrency window.
- Prove 75 default projects match their assigned seats, 75 own-namespace edit
  checks succeed, and 75 cross-seat reads are denied.
- Reclaim one workshop at a time and require zero residue across all three
  workshop scopes.
- Repeat the exact trio at least twice before the final rehearsal. Any defect
  first becomes a RED regression before it is corrected.

## Dated path to September 17

| Date | Required outcome |
|---|---|
| Sep 5 | Freeze the exact trio, capacity contract, evidence schema, and stop/go criteria. |
| Sep 6-7 | Complete AgentOps Gate A, including embeddings, shared observability, participant tabs, authorization, and reclaim. |
| Sep 8 | Gate B is GREEN-live; publish the five-seat catalog cap and preserve the build-83 storage exception. |
| Sep 9-10 | Add/qualify capacity or reduce topology, then complete Gate C at 25 seats. |
| Sep 11 | Run the first exact staggered 25 + 25 + 25 event trio. |
| Sep 12-13 | Run a second exact trio, tune only from evidence, and repeat any failed gate. |
| Sep 14 | Browser and operator rehearsal with representative participant identities and all lab journeys. |
| Sep 15 | Final capacity, NFS, image-cache, shared-model, route, entitlement, and cleanup rehearsal. |
| Sep 16 | Freeze catalog/image revisions and prepare the event orders, roster, owners, evidence directories, and rollback decisions. |
| Sep 17 | Recheck capacity, provision in the certified staggered order, retain all 75 seats, run the event, capture evidence, then reclaim sequentially. |

Sep 10 is the AgentOps 25-seat stop/go point. Sep 13 is the exact-trio stop/go
point. Missing either gate triggers the documented event contingency; it does
not justify silently raising the catalog limit or weakening validation.

## Proof model

### TDD and RED/GREEN

- Every newly found failure is captured as a failing automated regression or a
  stable live check before the fix.
- Preserve RED, GREEN-local, GREEN-integration, and GREEN-live outcomes with
  test IDs and evidence links.
- Do not promote `agentops-observability` from 1 to 5 or from 5 to 25 based on
  pod readiness alone.

### CDD and CBT

- Contract-test the catalog seat limit, whole-workshop Arena affinity,
  aggregate reservation, generated runtime inputs, workload/Showroom
  Applications, participant URLs, reclaim target, and zero-residue response.
- Component-test embeddings, Mortgage AI, database, MinIO, Grafana, MLflow,
  logging, DSPA, inference, Showroom, terminal, Console, entitlement gateway,
  and cleanup independently before the integrated participant journey.

### BDD

Given the exact three event workshops are assigned to their persisted certified
clusters only after the previous order is Ready, when 75 participants
concurrently complete their assigned lab journeys, then every functional and
isolation check succeeds and sequential reclaim leaves no managed resource in
any event workshop scope on any cluster.

### EDD and release rubric

Each run records commit SHA, image digests, catalog/content revisions, capacity
previews, order/workshop/session/namespace IDs, timestamps, collective
readiness, functional results, latency percentiles, node/NFS observations,
authorization checks, screenshots, audit events, and post-reclaim inventory.

The exact-trio release requires 100/100:

| Area | Points |
|---|---:|
| Exact catalog/content/image revisions | 10 |
| Capacity reservation and retained headroom | 15 |
| 75/75 collective readiness | 15 |
| All three participant journeys | 20 |
| Showroom, terminal, Console, and route behavior | 10 |
| Namespace and entitlement isolation | 10 |
| Shared models, embeddings, and observability stability | 10 |
| Sequential reclaim and zero residue | 10 |

Any critical row that is not GREEN-live scores zero and blocks release.

## Public-access boundary

The internal multi-cluster workshop path is the release baseline. Public access
is not certified by the existing 3x25 evidence. A temporary quick tunnel and a
changing hostname are not an event-grade dependency. Public participation can
be added only if one stable front door resolves each entitlement through its
persisted `cluster_ref`; every target independently passes TLS, private-origin
routing, Keycloak/OIDC, Showroom, WebSocket terminal, Console, 25-participant
burst, expiry, and reclaim checks by Sep 15. Otherwise the event must use the
certified internal/VPN access path.

## Event contingency

The target remains 25 AgentOps + 25 Serve LLMs + 25 Building an AI Agent. If
AgentOps misses its stop/go gate, do not represent a shared instructor demo or
a lighter substitute as a certified 25-seat AgentOps workshop. The organizer
may explicitly choose a reduced AgentOps format, but it must be labeled as a
contingency and retain the two already certified 25-seat workshops.
