# Next-iteration pathways and roadmap

This document parks improvements that are valuable after the current visual
Showroom-scale release gate. They are not blockers for completing the present
25-seat participant-experience certification unless explicitly stated.

## Immediate release gate

The dated release gate is now the September 17 fleet event candidate: 25
AgentOps seats, 25 Serve LLMs seats, and 25 Building an AI Agent seats. Orders
are staggered but all 75 participant environments remain active concurrently.
The capacity contract, AgentOps 1 -> 5 -> 25 promotion path, exact-trio proof
matrix, stop/go dates, and access boundary are defined in
`docs/september-17-three-workshop-readiness.md`.

The earlier three-workshop pilot proved the orchestration shape and both Intel
guided labs at 25 seats. AgentOps is the critical path and must not be promoted
past its measured live evidence. Public access remains a separate certification
gate; internal Arena access is the September release baseline unless the public
matrix is independently GREEN-live by Sep 15.

As of September 5, AgentOps passed its internal Launchpad-created one- and
five-seat gates, including Showroom, runtime credentials, concurrent
application journeys, shared Nomic embeddings, PostgreSQL-backed MLflow
isolation and tracing, DSPA with a service-ca TLS pipeline database, OpenShift
Logging ingestion/isolation, fault reclaim, and zero-residue normal reclaim.
Logging still needs durable object/block storage and production sizing, and
trusted public TLS is not certified.

The AgentOps 0.1.4 candidate co-locates its API and UI while preserving their
separate Services and routes. This reduces the steady topology from 13 to 12
pods per seat. Capacity now reserves 300 steady pods plus only the eight
rollout/bootstrap pods possible in a two-seat provisioning wave, instead of
multiplying a 17-pod peak envelope into 425 slots. This 308-pod calculation is
GREEN locally but remains a live-candidate estimate until the one- and
five-seat chart reruns confirm it. The qualified single Arena worker still
cannot admit 25 AgentOps seats. Per-seat DSPA and database isolation are
retained; sharing the project-scoped pipeline stack is not an approved shortcut.

The current candidate path dedicates Arena to AgentOps and re-certifies Oberon
for Serve LLMs. Brutus is registered and passed the one-, five-, and
25-seat internal gates with a measured three-pod contract. The 25-seat run
created 75 healthy pods, completed all 25 simultaneous three-tool journeys,
preserved namespace isolation, and reclaimed with zero residue. Its capacity
preview now supports 30 seats while retaining 20 percent headroom. The
integrated registry uses a retained 100Gi NFS claim and all three pinned digests
passed `Always` pull probes after a deliberate registry restart. Brutus remains
placement-disabled and reserved for emergency use; public access and Console
OIDC are separate gates.
Oberon needs eleven
additional protected slots before its live gate.

The Brutus one-seat run also measured the fleet prerequisites that must move
out of the ordering path: a 10m42s cold Showroom terminal-image mirror, a
resumable registry HTTP 408 while moving the solution-agent image, execution
cluster ingress-CA distribution, and a 300-second private model Route timeout.
The warm five-seat run initially proved concurrency but not durable supply.
Durability is GREEN-live in `evidence/brutus-persistent-registry-2026-09-05.json`,
and the deployed CA-verification plus internal 25-seat scale reruns are GREEN-live
in `evidence/brutus-agent-201-three-pod-certification-2026-09-05.json`.

## Pathway 1: provisioning performance

- Replace in-request workshop execution with a durable queue and bounded workers.
- Permit organizers to submit multiple orders while execution is safely staggered.
- Measure per-cluster seat, Argo sync, route-ready, and collective-ready latency.
- Tune Argo and worker concurrency from observed saturation rather than static limits.
- Preserve whole-workshop cluster affinity and fail-closed capacity reservations.

Measured baseline for 25 seats on 2026-08-26:

- Oberon: approximately 14 minutes 9 seconds
- Arena: approximately 2 minutes 35 seconds to 2 minutes 54 seconds

## Pathway 2: organizer readiness estimates

- Show predicted readiness time during capacity preview and order confirmation.
- Display queued, provisioning, validating, and collectively-ready timestamps.
- Calculate estimates from recent cluster/catalog percentiles rather than constants.
- Show confidence and ineligibility reasons in the portal and admin dashboard.
- Publish an organizer-facing workshop startup SLO only after repeated runs.

## Pathway 3: automated participant experience

- Add a namespace-scoped validation runner that uses the same permissions as the
  Showroom terminal without granting the central provisioner token-mint or exec rights.
- Validate every generated Antora page and personalized attribute.
- Run the documented workload exercise and require an HTTP 200 response/body.
- Capture browser screenshots and console errors for representative seats.
- Keep human visual review as the final release check for layout and usability.

## Pathway 4: scale graduation

- Repeat 25-seat visual certification three times.
- Certify 50 seats on Arena only after retained capacity headroom is measured.
- Certify 75 seats on Arena only after the 50-seat gate passes.
- Continue toward the fleet goals in `docs/three-by-seventy-five-capacity-plan.md`.
- Do not advertise a seat limit inferred only from allocatable cluster capacity.

## Pathway 5: production solution portfolio

Promote StarGate, DeepField, and GeoLux as production solution paths without
bundling all three into every participant seat. Launchpad remains the catalog,
placement, workshop, Showroom, handoff, and lifecycle control plane; each
solution retains its own repository, deployment, data, security, and release
ownership.

- **StarGate:** shared validation and operations service. Integrate Launchpad
  lifecycle evidence, readiness rubrics, capacity signals, failure classes, and
  gated remediation. Offer a guided operations journey only when the learning
  objective is platform reliability.
- **DeepField:** shared fleet observability and inference-intelligence service.
  Add a guided journey using scoped or synthetic signals to demonstrate signal
  compression, classification, routing, forecasting, and advisory remediation
  without exposing unrestricted fleet telemetry.
- **GeoLux:** governed agentic-inference solution. Add it after StarGate and
  DeepField contracts are stable, with a guided hypothesis, constraint,
  stability, routing, and replay journey backed by approved model endpoints.

Use the graduation sequence and ownership boundaries in
`docs/production-solution-pathways.md`. A solution is not production merely
because its UI is reachable from Launchpad; it must pass contract, security,
operations, visual journey, capacity, reclaim, and support gates.

## Pathway 6: self-service operations and auto-remediation

- Expand self-service from ordering to CI scaffolding, preview certification,
  tenant administration within policy, actionable failure explanations, and
  owner-scoped retry/reclaim.
- Normalize failure classes and evidence before automating mutations.
- Graduate each remediation independently through observe, recommend,
  approval-gated execution, and allow-listed automatic execution.
- Start with retry-safe session-scoped actions such as validation retry,
  Showroom resync, owned Route recreation, failed-seat retry, expired-session
  reclaim, and cleanup reconciliation.
- Require immutable target-cluster identity, idempotency, retry budgets,
  functional post-validation, audit records, circuit breakers, and escalation.
- Keep RBAC/Secret changes, cluster-scoped Operators, shared model deployment,
  infrastructure/DNS/certificates, capacity expansion, and ambiguous deletion
  behind human approval.
- Move long-running provisioning and remediation to durable workers so the
  platform can recover its work after API restarts.

The complete autonomy boundary and graduation sequence are defined in
`docs/self-service-and-autoremediation.md`.
