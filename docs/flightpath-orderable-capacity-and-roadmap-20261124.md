# Flightpath Orderable Capacity, Catalog Synopsis, and Roadmap

**As of 2026-11-24.** Live `launchpad-flightpath-candidate` catalog ConfigMaps,
`certification/catalog/`, `evidence/runs/`,
`staging-candidate-order-of-operations-20261016.md`, and the 2026-09-29
convergence roadmap.

> **Platform is scaled to zero** since 2026-11-16 (all Deployments `0/0`,
> CronJobs suspended, no Service endpoints, `labs.smg-helix.ai` 530). Data
> intact: both PVCs `Bound`. This is an **owner decision, not an incident** —
> capacity was reallocated to other projects and the platform can be restored
> on demand (recorded 2026-11-24). Replicas are pinned at `0` in the Deployment
> specs with no HPA, so a scale-up is not fought by anything.

## How to read the seat numbers

| Term | Meaning |
|---|---|
| **Cap** | `max_workshop_seats` in the deployed catalog item — what the order path accepts today |
| **Ladder** | `scale_profiles` in the certification contract — promotion targets, not completed proofs |
| **Evidence** | Highest seat count with a retained hashed run artifact, and its date |

All multi-seat evidence predates the mid-October image freeze. The strongest
5-seat dataset is `e2d78de` (2026-09-29); it is historical proof, not
current-revision proof.

**A cap of 1 is deliberate, not a defect.** Staging certifies one seat per
catalog. Larger caps are post-staging work — see the Roadmap.

## Catalog and capacity — 26 IDs

| Item | Lvl | Track | Cap | Ladder | Best evidence | Exposure |
|---|---|---|---|---|---|---|
| `agent-reliability` | 301 | Agentic | 1 | 1 | 5 seats 09-29 | public |
| `agentic-ai-101` | 101 | Agentic | 1 | 1 | 1 seat 10-06 | public |
| `agentic-ai-601` | 601 | Agentic | 1 | 1 | 1 seat 10-05 | internal only |
| `ai-sandbox` | 001 | Sandbox | 1 | 1, 5 | 5 seats 09-29 | public |
| `cpu-inference-serving` | 101 | Serve | **5** | 1, 5 | 5 seats 09-29 | public (alias) |
| `hybrid-fraud-detection` | 201 | Agentic | 1 | 1 | 5 seats 09-29; 25 seats 09-22 | public |
| `intel-llm-cpu-serving` | 101 | Serve | 1 | 1, 5 | 5 seats 09-29; **30 seats GREEN ×3** 09-15 | public — was fail-open, declared 11-24 |
| `intel-llm-tool-calling` | 201 | Agentic | 1 | 1 | 5 seats 09-29 | public — was fail-open, declared 11-24 |
| `intel-xeon6-agent-201` | 201 | Agentic | 1 | 1 | 5 seats 09-29; **30 seats GREEN ×3** 09-16 | internal |
| `multi-agent-quickstart` | 301 | Agentic | 1 | 1, 5, 25, 30 | 5 seats 09-29; 25 seats 09-06; **30 seats GREEN ×3** 09-16 | public_code |
| `network-operations-agent` | 301 | Agentic | 1 | 1 | 5 seats 09-29; 25 seats 09-24 | public |
| `openshift-operators-workshop` | 201 | OpenShift | 1 | 1, 5 | 5 seats 09-29 | public |
| `operate-agentic-blueprint` | 401 | Agentic | 1 | 1, 5, 25 | 25 seats 09-28 | public |
| `rag-on-xeon` | 101 | Serve | **5** | 1, 5 | 5 seats 09-29 | public (alias) |
| `scale-agentic-blueprint` | 501 | Agentic | 1 | 1 | 1 seat 10-09 | internal only |
| `sovereign-ai-101` | 101 | Sovereign | 1 | 1 | 1 seat 09-30 | internal |
| `sovereign-ai-201` | 201 | Sovereign | 1 | 1 | 1 seat 09-30 | internal |
| `sovereign-ai-301` | 301 | Sovereign | 1 | 1 | 1 seat 09-30 | internal |
| `virtualization-ai-foundations-101` | 101 | Virt+AI | 1 | 1 | 1 seat 10-01 | public |
| `virtualization-ai-201` | 201 | Virt+AI | 1 | 1 | 1 seat 10-01 | public |
| `virtualization-ai-301` | 301 | Virt+AI | 1 | 1 | 1 seat 10-01 | public |
| `virtualization-ai-401` | 401 | Virt+AI | 1 | 1 | 1 seat 10-02 | public |
| `virtualization-ai-501` | 501 | Virt+AI | 1 | 1 | 1 seat 10-02 | public |
| `smoke-test` | 001 | Diagnostic | — | — | — | **draft**, not orderable |
| `sovereign-ai-401` | 401 | Sovereign | 1 | 1 | — | **draft**, TDX/Trustee blocker |
| `sovereign-ai-501` | 501 | Sovereign | 1 | 1 | — | **draft**, TDX/Trustee blocker |

**23 active** = 21 participant-visible + 2 internal-only.

> "Declared 11-24" means the declaration is committed at HEAD **and applied to
> the live cluster** on 2026-11-24, including the candidate overlay copy that
> actually ships the item. Before that apply the three items were fail-open for
> public exposure; their certified scope is `[internal, public_code]`, so the
> apply changed the declaration, not the behaviour.

## Seats available today

| Ceiling demonstrated | Count | Items |
|---|---|---|
| **30** | 3 | `multi-agent-quickstart`, `intel-llm-cpu-serving`, `intel-xeon6-agent-201` |
| **25** | 6 | the 3 above + `hybrid-fraud-detection`, `network-operations-agent`, `operate-agentic-blueprint` |
| **5** | 12 | adds `agent-reliability`, `ai-sandbox`, `cpu-inference-serving`, `intel-llm-tool-calling`, `openshift-operators-workshop`, `rag-on-xeon` |
| **1** | 11 | `agentic-ai-101`, `agentic-ai-601`, `scale-agentic-blueprint`, `sovereign-ai-101/201/301`, `virtualization-ai-*` (5) |

**Powered on with today's config:** 19 experiences at 1 seat, 2 aliases at 5
seats, nothing above 5. But **10 items already hold five-seat-or-better
evidence and are capped by configuration, not capability**.
**`multi-agent-quickstart` already met its full 30 × 3 ladder** on 2026-09-16.

**What blocks more seats:** no current-revision multi-seat proof (everything
predates the mid-October image freeze); 25/30 ladders need 3 consecutive runs;
and inference headroom (`PILOT-PERF-002/003`), not node capacity, is the real
ceiling.

**But none of this is a staging defect.** `max_workshop_seats: 1` is the honest
number until a current-revision run replaces the September evidence. Seat
expansion is **Track B, post-staging** — see the Roadmap.

## What each experience teaches

**Foundations**
- `ai-sandbox` — OpenShift playground with console, terminal, IDE, and CPU model access. 8 h. No scripted curriculum.
- `openshift-operators-workshop` — Author namespaced CRs, watch an Operator reconcile, verify, prove cleanup. Declared vs. observed state.

**Agentic AI ladder**
- `agentic-ai-101` — One request end to end: proposal → bounded tools → labelled evidence → policy → human authority → reviewable record.
- `intel-llm-tool-calling` — The tool-calling protocol itself: schema, arguments, results, and refusals.
- `intel-xeon6-agent-201` — Build and tune a LangGraph + MCP solution advisor in an isolated namespace.
- `hybrid-fraud-detection` — Deterministic rules plus model inference: what "explainable" must mean when a decision is disputed.
- `agent-reliability` — Contain prompt injection, deny unauthorized MCP tools, cite evidence, degrade safely when inference dies.
- `multi-agent-quickstart` — Incident response with specialized agents; A2A, MCP, Kagenti, OpenTelemetry, guardrails, service auth. Widest seat ladder.
- `network-operations-agent` — Telecom alarm triage where every recommendation must cite its source.
- `operate-agentic-blueprint` — Day-two operations: correlate, deny, recover, and prove a controlled config change.
- `agentic-ai-601` — Graduated autonomy: how an agent earns broader action rights, and what evidence justifies each promotion.
- `scale-agentic-blueprint` — Production-shaped qualification: resilience trials and human-controlled promotion.

**Serve LLMs on Xeon**
- `cpu-inference-serving` — Shared Xeon inference, verify the endpoint, deploy a namespace-isolated RAG assistant. Proves useful inference needs no GPU.
- `intel-llm-cpu-serving` — The fuller 101: explore the endpoint, then build and test the RAG assistant.
- `rag-on-xeon` — Build and validate RAG with the model held constant, so retrieval is what is being learned.

**Sovereign / governed inference**
- `sovereign-ai-101` — Classification, deterministic policy, bounded dispatch, evidence receipts, refusal states. Refusal is designed, not improvised.
- `sovereign-ai-201` — Build a fail-closed inference boundary: residency, trust, schemas, Secrets, NetworkPolicy, typed outcomes, redacted evidence, reclaim.
- `sovereign-ai-301` — Challenge-bound workload identity, attestation and appraisal, independent authorization. TDX vocabulary.
- `sovereign-ai-401` *(draft)* — Operate a confidential trust lifecycle: attestation → appraisal → authorization → revocation → verification.
- `sovereign-ai-501` *(draft)* — Qualify a multi-node confidential fleet: policy rollout, attestation freshness, revocation, dependency failure, admission limits.

**Virtualization + AI**
- `virtualization-ai-foundations-101` — Trace one attributable request from a VM through platform networking to governed Xeon inference.
- `virtualization-ai-201` — Author and qualify the VM-to-AI contract: schema, guest client, Secrets, Service, NetworkPolicy, adapter validation, reclaim.
- `virtualization-ai-301` — Modernize a VM with governed AI without displacing operator authority.
- `virtualization-ai-401` — Day-two operations on hybrid VM and AI workloads: what breaks, what is observed, who decides.
- `virtualization-ai-501` — Qualify a governed VM inference fleet with evidence-backed human review.

## Roadmap

Two tracks. The seat work in this document belongs to **Track B**; it is
deliberately *not* part of staging.

| | **Track A — staging candidate** | **Track B — 5 seats (post-staging)** |
|---|---|---|
| Scope | 1 seat per catalog, truthful, reclaimable | Raise caps; prove 5/25/30; inference reservation |
| Owner doc | `staging-candidate-order-of-operations-20261016.md` | `roadmap-convergence-20260929.md`, LP-S037 |
| State | **critical path, open** | **gated — do not start without a new decision** |

The 2026-09-29 convergence roadmap is explicit: *"Every currently viable
catalog certified and manually orderable at one seat on Flightpath. Five-seat
proof remains retained scale evidence and is not a staging prerequisite"*, and
catalogs *"remain deliberately capped at one certified seat."* Targeted
five-seat reruns appear only inside LP-S037, one of four lanes that require a
new product-owner decision **after** staging acceptance.

### Track A — staging candidate

| Phase | Work | State |
|---|---|---|
| **0** | Owner decisions: x/crypto GO-2026-5932 disposition; Console cutover window | Brief 2 **closed by live check 11-24** — no override exists; Brief 1 **1 signature needed** |
| **1** | Keycloak 26.8.1 isolated upgrade + DB compatibility proof; virtualization-ai-501 narrow-pane layout | **closed** (2026-10-16) |
| **2** | Vendor-pending images: terminal, backend | **blocked on vendors**; counts corrected below |
| **3** | Staged catalog pins; exact-commit regression; current-revision public browser proofs | pins + regression **closed**; public proofs **open and failing** |
| **4** | Console verify-or-cutover; full acceptance sweep with zero residue | Console **verified native 11-24, no mutation needed**; sweep still **unverified** |

**Phase 0** is down to one signature, and it is Brief 1's. `docs/phase-0-owner-decisions-20261124.md`
carries both briefs. Brief 1 asks to accept GO-2026-5932 with scope (the two
unrated matches are `openpgp` code linked into `oc` and `helm` via
`containers_image_openpgp`, with no platform path reaching it in either and no
fixed version in any release). Brief 2 was a 90-minute Console window that opened
with a read-only check — **and the check ran on 2026-11-24: the operator has no
`spec.route` override and no `console-custom` route exists, so the window is
void.** No mutation was needed and none was made. The Flightpath/network
sign-off waived on 2026-11-24 was therefore never exercised.

Two corrections to the earlier reading, both now in the brief. **Signing does
not clear the backend gate:** the gate blocks on the full inventory, so the
disposition removes 2 of 37 blocking findings and leaves 35 High. And the
advisory is **not backend-only** — the count of two matches is two *binaries*,
`oc` and `helm`, and the showroom-terminal image builds `skopeo` with the same
`containers_image_openpgp` tag and carries the same unrated finding. Brief 1
covers the two backend binaries only; `skopeo` is participant-invocable, where
the reachability argument is weakest, and needs its own disposition.

**Phase 1 is closed — the doc previously had it wrong.**

- Keycloak 26.8.1 is **promoted and live**, not merely proven:
  `evidence/convergence/keycloak-stage-promotion-20261016.yaml`
  (`ISOLATED-PROOF-PASSED-AND-PROMOTED`, Deployment `2/2`,
  `live_service_changed: true`, realm/client/user counts unchanged 2/16/53).
  The full browser login-flow proof is folded into the Phase 4 sweep.
- The virtualization-ai-501 narrow-pane layout is **closed**:
  `evidence/convergence/v501-layout-canary-20261016.yaml` records
  `PASSED-EMBEDDED-PANE-CONTROLS-REACHABLE-ZERO-RESIDUE` at `3f9d8c1`, all three
  qualification controls reachable, zero residue.

**Phase 2 counts were stale.** `image-security-revalidation-20261020.yaml` is the
current baseline: backend full inventory `{Critical 0, High 35, Unknown 2}` with
**2** fixable High; terminal `{Critical 31, High 350, Unknown 10}` with **63**
fixable (4 Critical, 59 High). The `25 High` figure quoted in older documents is
explicitly historical, not the present scan.

**"Fixable" is a scanner claim, not an errata.** The gate reads Grype's
`fix.state`, so `fixed: 2` means the scanner database knows a newer package
version exists somewhere upstream — not that Red Hat shipped a fix for RHEL 9.
`backend-vendor-states-20261020.json` queried 11 advisories and found every one
still `Affected`, and an isolated read-only `dnf` dry run refused to remove
`python3.9` because DNF and Yum require it. So "fixable" had to be checked
item by item before anything could be done with it — the 30 RPM High matches
behind 11 distinct advisories have no errata to install, and a forced package
upgrade would be a protected-package override, not a fix.

**The two are named, and they resolve differently.** The fixable report body was
retrieved from CI run 39473152288; `vulnerability-report-fixable.json` hashes to
`cbb1ec5e…`, matching the value recorded in the repo, so it is the report the
gate actually used. Both High findings are
`github.com/distribution/distribution/v3` at the 2023 pseudo-pin, fixed only in
`v3.1.0`:

- `GHSA-f2g3-hh2r-cwgc` (GO-2026-4942) affects
  `registry/storage/cache/redis`. That package is absent from the `oc` symbol
  table, and govulncheck's only record for it is module-level with no frame. It
  is not linked.
- `GHSA-3p65-76g6-3w7r` (GO-2026-5094) carries **no symbol data** in the
  advisory, so no scanner can prove absence and govulncheck reports it at
  package level across the linked client. The pull-through cache
  implementation, `registry/proxy`, is also absent from the binary, and the
  exploit needs a configured upstream credential store that a client never has.
  It closes on that applicability argument, not on symbol evidence.

The harness already states both as surfaces rather than prose: the same run's
`client-symbol-inventory.json` records `distribution-proxy` and
`distribution-redis-cache` with `named_symbols_present: false` and zero matches
over 155,403 symbols at `8b8fc909`. (The same file records `archive-extraction`
as **present**, 66 symbols — so the check discriminates rather than returning
false for everything.)

Neither closes by upgrading: `v3.1.0` drops registry client packages
`openshift/library-go` imports — tried in `d3274b41`, reverted in `506e739a`.
That is the "review the two" half of the 2026-11-24 split; the remaining 33 High
go to vendor wait.

**Phase 3 — half closed.** The staged pins are committed (`a1d1eb67`,
`647497bc`, `746e9e71`, all ancestors of HEAD) and the exact-commit regression is
GREEN (2921 passed / 0 failed / 27 skipped at `a38f1722`). What remains is the
public proof set, and it is the hard part:

| Item | Latest evidence | Result |
|---|---|---|
| `virtualization-ai-401` public journey | `evidence/runs/public-401-journey-20261016.json` | **failed** — `terminal_alive_marker_executed` and `embedded_console_loaded` both false |
| `virtualization-ai-501` public | `v501-story-api-canary-20261015.yaml` | `complete_public_certification_claimed: false`; `current_public_browser_validation: pending` |
| `sovereign-ai-201` public | `catalog/sovereign-ai-201-flightpath-public-one-seat-20261001-r1.json` | GREEN on 2026-10-01, **predates the image freeze** |

The 401 result is **not a clean product signal**. Its artifact carries two empty
booleans and no diagnostics; the harness that produced it is not in the repo
(grepping its step names finds only the artifact); and a same-revision browser
review one day earlier passed both checks — noting that the console only loaded
"after delayed initial load". The last **certified** public browser pass on this
item is 2026-10-02 on `38e2fa91`, before the re-pin, and it records
`terminal_websocket_handshake: true` and `openshift_console_embedded: true`.
Treat 2026-10-16 as **unexplained non-determinism**, not evidenced regression.

The reproducible instrument already exists:
`scripts/catalog_certification.py run … --seats 1 --exposure-policy public_code`
emits named sub-checks and a hash, which is what the 2026-10-02 run was. The
ad-hoc journey should be retired or given diagnostics and checked in.

**Phase 4 — the Console half is now verified, read-only.** The contradiction was
between `flightpath-native-console-repair-20261014.yaml` (repair deployed,
browser-verified) and `staging-candidate-freeze-20261016.yaml` (a hostname
cutover still listed as pending). Checked live on 2026-11-24:

| Object | Observed |
|---|---|
| `console.operator.openshift.io/cluster` → `spec.route` | `{"hostname":"","secret":{"name":""}}` — **no override** |
| `openshift-console` routes | `console` and `downloads` only; **no `console-custom`** |
| Both Console routes | `*.apps.flightpath.fm2aihpcsed.com` |
| Console operator | `Available=True`, `Progressing=False`, `Degraded=False` |
| Console pods | running, `1/1` |

So the October native-route repair is the live state. The `530` on
`labs.smg-helix.ai` is the Cloudflare tunnel having no pod, not the Console
holding the host. The full acceptance sweep is still unverified: nothing under
`evidence/` postdates **2026-10-20 15:24**, and it has no retained artifact.

**Also Track A — live checks, not repo checks**

- ~~Explain and document the 2026-11-16 scale-to-zero~~ — **answered
  2026-11-24** by the Launchpad owner: deliberate, capacity reallocated to other
  projects, reversible on demand. Recorded as a decision, not an incident. It no
  longer gates Phase 4; a powered-off platform still cannot host a gate run, so
  the sweep waits for a power-on rather than a decision.
- Reconcile the orphan `network-operations-agent-catalog` ConfigMap mounted at
  the same path as the Git-managed v0.2.1 item.
- Dispose of `network-operations-demo`, a public-route copy of a catalog app
  running since 2026-09-25 outside the Launchpad lifecycle.

**Exposure declarations — closed** (`a2f7c18e`, `cfd5bb62`, `21487266`).
Three active items omitted `metadata.allowed_exposure_policies`, not two, and
their certification contracts authorise `[internal, public_code]`, so the
runtime default was **undeclared**, not over-permissive. `intel-llm-cpu-serving`,
`intel-llm-tool-calling`, and `rag-on-xeon` now declare the certified value.

A fourth gap was deployment-path only: the candidate overlay ships a full copy
of the `intel-llm-cpu-serving` item as the `flightpath-candidate-serve-llms-catalog`
ConfigMap, so fixing the base file alone left the **deployed** item fail-open.
The overlay now declares it too.

**Applied live 2026-11-24.** Three ConfigMaps (`canonical-intel-llm-tool-calling-catalog`,
`canonical-rag-on-xeon-catalog`, `flightpath-candidate-serve-llms-catalog`) were
patched from the rendered overlay and the backend was rolled, because those
mounts use `subPath` and do not track ConfigMap updates. Verified through the
backend's own `FileCatalogAdapter` against the live mount:

```
intel-llm-cpu-serving  -> ['internal', 'public_code']
intel-llm-tool-calling -> ['internal', 'public_code']
rag-on-xeon            -> ['internal', 'public_code']
sovereign-ai-301       -> ['internal']            (withdrawn 10-16, unchanged)
total: 28 items                                    (unchanged)
```

Six other ConfigMaps also differ from the rendered overlay, but only in
`metadata.source_references` (evidence paths) — not exposure, not seat ceilings.
Those were left alone; applying them is a content change nobody has asked for.
`network-operations-agent-catalog` still exists live with no Git source, as
noted above.

The six catalog/certification disagreements are aligned certification ← catalog,
in the direction the evidence supports rather than by preference:

| Group | Items | Why the certification side was stale |
|---|---|---|
| cert `[internal]` → `[internal, public_code]` | `agent-reliability`, `hybrid-fraud-detection`, `virtualization-ai-201`, `-301`, `-foundations-101` | Enabled for public on 2026-10-01 with catalog + intake + test changed together; the cert edit was skipped. Siblings enabled in the same wave (`virtualization-ai-401/501`, `agentic-ai-101`, `network-operations-agent`) did get it. All five hold `GREEN-live-public-exposure` runs on 2026-10-01/02. |
| cert `[internal, public_code]` → `[internal]` | `sovereign-ai-301` | `746e9e71` withdrew public access on 2026-10-16 (`public_max_workshop_seats: 0`, test asserts internal-only) but left the cert over-broad. |

**This authorises; it does not re-certify.** The public proofs predate the
2026-10-16 image freeze, and the three virtualization items have been re-pinned
since, so a current-revision public one-seat run per item is still required
before claiming public readiness.

Two guards now prevent recurrence: catalog exposure must be a subset of the
certification contract, and every `*.catalog-item.yaml` copy in the candidate
overlay must match its base item. Neither check existed, which is how all six
drifts and the deploy-path gap survived.

**Still open on exposure hygiene** (metadata inconsistencies, not gate items):
the five re-authorised items carry no `public_access_certification_stage` or
`public_max_workshop_seats`, unlike their four siblings; and
`certification/catalog/multi-agent-quickstart-flightpath.yaml` duplicates the
`catalog_item_id` of `multi-agent-quickstart.yaml`, so two contracts claim one id.

**Staging accounting:** the 2026-09-29 rollup recorded 210 tasks, 0 GREEN-live,
181 RED after fail-closed rollup. Phases 1 and half of 3 have since closed; the
rollup has not been re-run, and nothing under `evidence/` postdates 2026-10-20.

### Track B — 5 seats per item

Not started, and correctly so: **`max_workshop_seats: 1` is the honest number
today.** Raising a cap before a current-revision run would make the catalog
advertise something it cannot demonstrate — the exact failure the staging gate
exists to prevent.

| Step | Unlocks | Prerequisite | Effort |
|---|---|---|---|
| **B1** | 10 more items at 5 seats | Fix 4 hardcoded seat ceilings; raise `max_workshop_seats` on 10 items; add `5` to 5 of their ladders; raise `public_max_workshop_seats` on 2 | S |
| **B2** | Believable 5 seats | Current-revision 5-seat GREEN-live run per item, zero residue | M (rerun) |
| **B3** | *Safe* 5 seats | Inference reservation per workshop, burst headroom test, real admission or enforced per-seat quota | **L — real engineering** |
| **B4** | 25 seats for 4 items | 3 consecutive current-revision 25-seat runs, on top of B3 | L |
| **B5** | 30 seats for `multi-agent-quickstart` | Ladder already met 2026-09-16; needs current revision plus B3 | M |
| **B6** | `sovereign-ai-401/501` at any seat count | Intel TDX + Trustee availability | — |

**B1 — the four hardcoded ceilings**

| File | Line | Behaviour |
|---|---|---|
| `services/catalog_onboarding.py` | 215 | emits `max_workshop_seats: 1` |
| `services/catalog_onboarding.py` | 1237 | emits `max_workshop_seats: 1` |
| `services/catalog_onboarding.py` | 1304 | raises if `!= 1` (discovery draft) |
| `services/catalog_intake_candidate_policy.py` | 132 | finding if `!= 1` |

`services/catalog_certification.py:292` also requires any onboarding ceiling to
be a declared `scale_profiles` entry, so the ladder must land before the cap —
which is the correct order. Runtime enforcement needs **no change**:
`_validate_workshop_seat_limit` (`provisioning.py:1766`) already takes the
minimum of the platform env, catalog max, and public max, and restricts
overrides to internal workshops at the next declared promotion step.

**B3 — why "safe" is engineering, not configuration**

- **No capacity admission exists.** `check_capacity`
  (`adapters/openshift/pool.py:47`) ignores its arguments and only asks whether
  the service account can create namespaces; `reserve()` writes to process
  memory. Nothing on the order path can refuse an order.
- **The shared model is the ceiling, not the nodes.**
  `granite-3.2-8b-tools` requests **78 CPU cores and 64 Gi per replica**. Five
  replicas is the stable setting — 390 cores — and a sixth will not schedule.
  Seat pods (~475m / 768Mi each) are cheap by comparison: 105 seats cost
  roughly 50 CPU and 80 Gi.

### Neither track — production gate

HA Postgres, backups and DR drills; production edge and identity HA; WAF; pen
test; load/soak/rollback; SLOs and paging; AI gateway and model registry;
cost/attribution telemetry; privacy and licensing; rate cards and GTM
ownership. Deferred/production-scale: hybrid-cloud federation, ACM/GitOps fleet
registration, residency and disconnected placement, cross-provider degradation
certification, provider-aware FinOps, rapid cluster onboarding, independent
Showroom delivery.

**Powered on today: 21 participant experiences — 19 at one seat, 2 aliases at
five. Ten items already hold five-seat-or-better evidence and are capped by
configuration rather than capability — but that gap is a post-staging question,
not a staging defect, and `1` is the truthful number until a current-revision
run replaces the September evidence.**
