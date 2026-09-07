# September 17 agentic three-workshop readiness gate

## Approved event outcome

On **September 17, 2026**, Launchpad must support three separate 25-seat
workshop orders. Provisioning is staggered, but all 75 participant seats must
remain usable concurrently.

AgentOps has been replaced in this event candidate by
`multi-agent-quickstart`. AgentOps remains available as a five-seat pilot; its
prior readiness contract and RED 25-seat capacity evidence remain immutable.

| Provision order | Catalog item | Seats | Current evidence | Candidate target |
|---|---|---:|---|---|
| 1 | `multi-agent-quickstart` | 25 | GREEN-live-25 three consecutive times on Arena | Arena |
| 2 | `intel-llm-cpu-serving` | 25 | GREEN-live-25 on Arena | Arena |
| 3 | `intel-xeon6-agent-201` | 25 | Earlier Arena 25-seat pass; current compact release passed 25 on Brutus | Arena, with a current-release regression |

The order is **Multi-Agent first**, Serve LLMs second, and Building an AI
Agent third. The Multi-Agent workshop has the longest measured provisioning
time, so starting it first preserves the most recovery time. Do not submit the
next order until every seat in the preceding workshop is Ready. Do not reclaim
an earlier workshop while creating the next one.

## Why this substitution is materially safer

The old event candidate required 25 AgentOps seats. That workload is proven at
five seats but its 25-seat reservation cannot fit on the currently qualified
Arena worker topology with protected headroom. The replacement Multi-Agent
workshop uses shared model serving and reserves two seat pods instead of the
12 steady seat pods required by the optimized AgentOps candidate.

Multi-Agent catalog v0.2.5 has three consecutive 25-seat GREEN-live runs. In
each run, every seat opened its Showroom pages, used its participant UI, ran
the three-agent workflow against a real model, exercised MCP and guardrails,
applied and rolled back the Track 2 learner policy, proved namespace isolation,
revoked its model key, and reclaimed with zero residue.

## Revised capacity contract

| Workshop | CPU | Memory | Pod slots | Declared seat storage |
|---|---:|---:|---:|---:|
| Multi-Agent, 25 seats | 30,000m | 51,200 MiB | 50 | 0 GiB |
| Serve LLMs, 25 seats | 16,625m | 37,200 MiB | 50 | 0 GiB |
| Building an AI Agent, 25 seats | 10,375m | 22,800 MiB | 75 | 0 GiB |
| **Event total** | **57,000m** | **111,200 MiB** | **175** | **0 GiB** |

With 20 percent workload headroom, the admission target is 68,400m CPU,
133,440 MiB memory, and 210 pod slots.

The Arena snapshot taken on September 6/7 observed two schedulable workers,
500 total worker pod slots, and 216 active worker pods. Holding 20 percent of
worker pod capacity in reserve leaves **184** additional slots. The event's
175-slot reservation therefore fits that snapshot with only nine slots left
inside the protected ceiling.

This is intentionally a narrow **candidate**, not a capacity guarantee. The
current free Arena capacity must be measured live immediately before every
rehearsal and event order. Admission must fail closed if active pod count,
requested CPU or memory, node readiness, model health, image availability, or
temporary rollout demand no longer fits the protected envelope.

## Evidence boundary

The earlier Arena pilot in
`evidence/arena-staggered-three-workshops-2026-09-04.json` proved the platform
shape: three staggered 25-seat orders, 75 retained participant environments,
concurrent functional use, authorization isolation, and zero-residue reclaim.
It included Serve LLMs and Building an AI Agent, but used LLM Tool Calling as
the third workshop.

The Multi-Agent promotion in
`evidence/multi-agent-quickstart-25-seat-promotion-2026-09-06.json` proves its
current 25-seat release independently. These results make the revised exact
trio eligible for rehearsal; they do not replace the exact combined proof.

Public access is not certified for this event candidate. The first rehearsal
uses internal/VPN access so public DNS, Cloudflare quick-tunnel lifetime,
Keycloak, and Console OIDC cannot be confused with workload-scale results.

## Exact-trio GREEN-live procedure

1. Record commit SHA, catalog versions, image digests, model routes, Arena node
   conditions, active pods, requested resources, and admission output.
2. Provision Multi-Agent 25 and wait for all 25 seats to cross the common
   readiness barrier.
3. Provision Serve LLMs 25, wait for all seats, and retain Multi-Agent.
4. Provision Building an AI Agent 25, wait for all seats, and retain the other
   50 environments.
5. Start the 60-minute concurrent hold only when all 75 seats are Ready.
6. Exercise all 75 participant journeys concurrently. Validate Showroom,
   terminal namespace identity, workspace UI, real LLM output, required tools,
   and cross-seat and node denial.
7. Capture shared model request latency, queue depth, failures, and HTTP status
   during the concurrent burst. A running pod is not functional evidence.
8. Reclaim one workshop at a time and verify model-key revocation plus zero
   remaining namespaces, Routes, RoleBindings, PVCs/PVs, Secrets, and Argo CD
   Applications belonging to the run.
9. Repeat the exact trio. Any discovered defect first becomes a failing test
   and RED evidence before correction and rerun.

## Red/green matrix

| Gate | RED baseline | Required GREEN-live evidence |
|---|---|---|
| Exact catalog revisions | Prior proofs span different revisions and workshop combinations | All three orders record the pinned event revisions and digests |
| Capacity | Point-in-time margin is only nine protected pod slots | Preflight and revalidation pass immediately before each order |
| Provisioning | No exact revised trio has run together | 25 + 25 + 25 Ready through staggered orders |
| Functional behavior | Pod readiness alone proves nothing | 75 participant journeys complete with real model responses |
| Authorization | Combined-run isolation is not yet recorded | Every seat can edit only its assigned namespace; cross-seat and node access are denied |
| Soak | No exact-trio 60-minute hold | All seats and model routes remain healthy for 60 minutes |
| Cleanup | Exact revised trio has not been reclaimed | Every generated resource and model key is gone with zero residue |
| Public access | Public access is not certified | Remains out of scope for the internal event rehearsal |

## Release rubric

The event candidate requires 100/100: 15 points for immutable contracts and
artifacts, 15 for placement and capacity, 20 for provisioning/readiness, 25
for participant functionality, 15 for authorization/isolation, and 10 for
cleanup and repeatability. Any failed critical cell keeps the event candidate
RED regardless of the numerical score.

The next gate is the **exact agentic trio live rehearsal on Arena**. AgentOps
continues separately at a maximum of five internal seats until its own 25-seat
capacity and architecture gates are satisfied.
