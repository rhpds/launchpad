# September 17 three-workshop readiness gate

## Event outcome

On **September 17, 2026**, the Launchpad execution fleet must support these
three separate workshop orders. Provisioning remains staggered, but all 75
participant seats must remain usable concurrently:

| Provision order | Catalog item | Participant seats | Current release state | Candidate target |
|---|---|---:|---|---|
| 1 | `agentops-observability` | 25 | RED: five-seat Arena gate failed, limited to one seat | Arena after topology reduction/capacity repair |
| 2 | `intel-llm-cpu-serving` | 25 | GREEN-live-25 on Arena | Oberon after re-certification |
| 3 | `intel-xeon6-agent-201` | 25 | GREEN-live-25 on Arena | Brutus after onboarding and certification |

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
Calling. It also does not certify public access or the proposed Brutus/Oberon
placement. Therefore the previous run proves the Launchpad orchestration
pattern, not the September 17 release candidate.

## Declared capacity envelope

The reservation below comes from the catalog contracts and the measured
AgentOps one-seat footprint. It excludes shared model and Launchpad control
plane services that are already running.

| Workshop | CPU | Memory | Pod slots | Declared seat storage |
|---|---:|---:|---:|---:|
| AgentOps, 25 seats | 62,500m | 179,200 MiB | 375 | 750 GiB |
| Serve LLMs, 25 seats | 16,625m | 37,200 MiB | 50 | not declared by catalog |
| Building an AI Agent, 25 seats | 10,375m | 22,800 MiB | 100 | not declared by catalog |
| **Event total** | **89,500m** | **239,200 MiB** | **525** | **at least 750 GiB** |

Admission must retain at least 20 percent additional headroom for scheduling,
operator activity, model services, temporary rollout overlap, and measurement
error. The protected target is therefore 107,400m CPU, 287,040 MiB memory, 630
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
| Running pods on workers | 193 |
| Unrequested worker CPU | 336,989m |
| Unrequested worker memory | 1,281,934 MiB |
| NFS free space reported | 6.5 TiB |

CPU, memory, and NFS fit the event reservation. Pod slots do not. The current
193 worker pods plus 525 declared event pods would require 718 slots; applying
the event's 20 percent protection requires 823. One additional 250-pod worker
would provide 750 total slots and fit the unprotected estimate, but not the
protected target, so the recommended event path is **two additional 250-pod
workers**.

A pilot-only alternative is to add targeted tolerations to Launchpad workloads
so selected participant pods can use the three otherwise idle control-plane
nodes. That supplies enough aggregate slots but creates control-plane
availability risk and needs its own load, eviction, API-latency, rollback, and
failure certification. It must not be enabled as an incidental chart change.

Scaling down unrelated deployments cannot solve this constraint: even an
otherwise empty two-worker pool cannot place all 525 declared event pods.
Running the workshops sequentially also does not meet the
requirement because all 75 participants must use the labs concurrently.

### Live fleet decision — September 5 after the AgentOps five-seat run

The corrected AgentOps build removed the PostgreSQL restart defect and the
workshop reclaimer found every persisted session. It still failed live: the
first four seats concentrated on `rhgnr1`, which stopped posting Ready at about
239 active pods. The fifth seat then failed closed before namespace creation
because the required model endpoint was unreachable. Cleanup reached zero
residue only after bounded removal of stale pod records, two orphan Argo hook
finalizers, and four Released NFS PVs. The five-seat gate remains RED; see
`evidence/agentops-five-seat-red-live-build77-2026-09-05.json`.

Current pod-slot snapshots and the standard 20 percent reserve produce this
candidate fleet assignment:

| Cluster | Schedulable pod slots | Active worker pods | Additional slots after reserve | Candidate event role |
|---|---:|---:|---:|---|
| Arena | 500 | 220 after cleanup | 180 | AgentOps only, after redesign or added stable capacity |
| Brutus | 250 | 109 | 91 | Building an AI Agent; currently nine slots short of its 100-slot peak contract |
| Oberon | 500 | 359 | 41 | Serve LLMs; currently nine slots short of its 50-slot peak contract |

Brutus is not registered as a Launchpad target and currently lacks the
AgentOps/RHOAI operator set, but it has ample CPU and memory for a lightweight
workshop. Oberon is disabled for placement and must be re-certified before it
hosts event seats. The preferred three-cluster path is therefore:

1. Keep Arena dedicated to AgentOps and reduce the per-seat topology by moving
   DSPA, pipeline database, MinIO, Grafana, and other safe components to one
   workshop-scoped shared stack, or add stable worker capacity.
2. Onboard Brutus and remove at least nine baseline pod slots (or reduce the
   Building an AI Agent peak contract) before its 1 -> 5 -> 25 certification.
3. Re-enable Oberon only after removing at least nine baseline pod slots and
   passing Serve LLMs 1 -> 5 -> 25 plus full reclaim.

No catalog limit or target override changes until those measurements are
GREEN-live. Placement must include per-node pod, CPU, memory, taint, topology,
and recent Ready-transition checks; aggregate cluster totals are insufficient.

## Critical path: AgentOps 1 -> 5 -> 25

Serve LLMs and Building an AI Agent already have 25-seat live evidence. The
release critical path is AgentOps, which stays draft and capped at one seat
until each gate is green.

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
every internal pipeline hop is still required before production. Before Gate B,
the `1x.demo` NFS/MinIO logging topology remains a pilot boundary. Arena has
only two storage-capable workers; a supported internal ODF deployment requires
three. The controlled five-seat certification can retain the pilot while it
measures ingestion, query latency, restarts, and storage growth, but production
activation still requires durable S3-compatible object storage, dynamic block
storage, and production sizing. Evidence is in
`evidence/agentops-mlflow-postgres-live-2026-09-05.json` and
`evidence/agentops-pipeline-database-tls-live-2026-09-05.json`.

### Gate B: five AgentOps seats

- Use the admin-only certification override to request exactly the next
  declared promotion target while the normal catalog maximum remains one.
- Provision five seats through a single workshop order.
- Require 5/5 collective readiness and five successful concurrent participant
  journeys, including embeddings, an agent exchange, a trace, metrics, logs,
  an evaluation, and a pipeline check.
- Measure NFS consumption and latency, shared embedding/model saturation,
  operator/API throttling, pod restarts, and reclaim duration.
- Reclaim the workshop and require zero residue.

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
| Sep 8 | Repeat Gate A from a clean state and complete Gate B with five seats. |
| Sep 9-10 | Correct any RED results, repeat five seats if needed, then complete Gate C at 25 seats. |
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
