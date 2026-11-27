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
| **0** | Owner decisions: x/crypto GO-2026-5932 disposition; Console cutover window | **closed** — Brief 2 by live check 11-24 (no override exists); Brief 1 signed 11-27 with its limits recorded. The backend gate itself is still blocked by the vendor-wait findings |
| **1** | Keycloak 26.8.1 isolated upgrade + DB compatibility proof; virtualization-ai-501 narrow-pane layout | **closed** (2026-10-16) |
| **2** | Vendor-pending images: terminal, backend | backend **vendor-wait**; terminal **blocked on a gate decision, not on vendors** — see below |
| **3** | Staged catalog pins; exact-commit regression; current-revision public browser proofs | pins + regression **closed**; public proofs **open and failing** |
| **4** | Console verify-or-cutover; full acceptance sweep with zero residue | Console **verified native 11-24, no mutation needed**; sweep still **unverified** |

**Phase 0 is closed.** `docs/phase-0-owner-decisions-20261124.md` carries both
briefs, and both are now resolved. Brief 1 accepted GO-2026-5932 with scope on
2026-11-27: the two unrated matches are `openpgp` code linked into `oc` and
`helm` via `containers_image_openpgp`, with no platform path reaching it in
either and no fixed version in any release. The signed record is
`evidence/convergence/backend-openpgp-advisory-disposition-20261124.yaml`.
Brief 2 was a 90-minute Console window that opened with a read-only check —
**and the check ran on 2026-11-24: the operator has no `spec.route` override and
no `console-custom` route exists, so the window is void.** No mutation was
needed and none was made. The Flightpath/network sign-off waived on 2026-11-24
was therefore never exercised.

What Brief 1's signature binds is in the file rather than left to inference. It
binds the two October scans, and **neither digest was ever published**: a
registry check at signing time found both absent, with `git-27b6d2b1`
(2026-10-14) still the newest candidate. The signature therefore documents a
reviewed build; it does not clear a pullable artifact, does not clear the
scanner gate — which reads enumerated `risk-acceptance/v1` triples and not this
schema — and reopens on the next promoted backend build by construction. The
30 RPM High matches behind 11 advisories and the 3 non-fixable Go findings are
untouched and remain vendor-wait.

Two corrections to the earlier reading, both now in the brief. **Signing does
not clear the backend gate:** the gate blocks on the full inventory, so the
disposition removes 2 of the 37 blocking findings measured on 2026-11-24 and
leaves 35 High; 2 of those were fixable and have since been fixed, leaving the
33 vendor-wait findings. And the advisory is **not backend-only** — the count of
two matches is two *binaries*, `oc` and `helm`, and the showroom-terminal image
builds `skopeo` with the same `containers_image_openpgp` tag and carries the
same unrated finding. Brief 1 covers the two backend binaries only; `skopeo` is
participant-invocable, where the reachability argument is weakest, and needs its
own disposition.

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
explicitly historical, not the present scan. Note that the terminal half of this
baseline describes an **unpublished** build — the deployed digest and its
correct counts are below.

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

**The terminal was measured wrong, and the error was ours.** Every terminal
number in this document — the `31 Critical / 350 High / 10 Unknown` above
included — describes `cefd6a5a`, a build that was **never published**
(`image_published: false`). The repository `quay.io/rh-ee-jkershaw/launchpad-showroom-terminal`
has exactly one active tag, `pilot-2026-09-17` → `324dc5c4`, and no retained
scan named that digest before 2026-11-24. So the gate was correctly blocking a
build nobody could pull, while the image participants actually ran had never
been scanned at all.

Scanned on 2026-11-24 with the same grype version as CI (0.97.1) and a current
database (schema v6.1.10, built that morning), twice — once from a
`docker-archive`, once from the registry reference — with byte-identical
findings. The registry scan is the signature-grade one because it records the
true `manifestDigest`:
`evidence/runs/terminal-deployed-scan-324dc5c4-20261124.json`
(`report_sha256 6c377e0b…`).

| | deployed `324dc5c4` | unpublished `cefd6a5a` | rebuilt projection |
|---|---|---|---|
| Critical | **112** | 31 | **3** |
| High | **1125** | 350 | **130** (8 CLIs only) |
| Unknown | 17 | 10 | 7 (8 CLIs only) |
| total matches | 2957 | 1219 | 226 (8 CLIs only) |
| distinct High/Critical ids | 255 | 92 | — |
| Criticals with a fixed version | **112 of 112** | 29 of 31 | 3 of 3 |

The counts are not directly comparable — the 10-20 scan used a five-week-older
database — but the direction is not subtle: the deployed image is **3.6× worse
on Criticals**.

**It is a stale image, not a compromised one.** `324dc5c4` predates the entire
October refresh, so participants have been running exactly the things that
refresh removed:

| | deployed | HEAD before this change |
|---|---|---|
| `odo` | **still present** — 22 Critical / 130 High by itself | removed 2026-10-16 |
| `skopeo` | 1.22.2, vendor `/usr/bin` | 1.24.1, source-built |
| `oc` / `kubectl` | 4.20.32, go1.24.13 | 4.22.18 |
| `kn` | v1.15.0, **go1.22.11** | v1.23.0 |
| `tkn` | 0.42.0, go1.24.6 | v0.46.1 |
| `tkn-pac` | 4.11.2 | v0.52.0 |
| `roxctl` | 4.11.5 | 4.11.5 |

111 of the 112 Criticals are `go-module` findings inside the nine Go binaries it
carries; exactly one is an RPM (`ca-certificates`, `CVE-2026-114406`). All 112
Critical matches carry a fixed version, and the High/Critical fix states are
`fixed 1187 / not-fixed 43 / unspecified 6 / wont-fix 1`. This is a pinning
problem, which is why it is worth fixing now rather than waiting.

**The fix is committed, and it lands at 3 Critical.** `097fb62b` moves the
pinned artifacts to the current vendor releases — `oc`/`kubectl` 4.22.23
(go1.25.14 → go1.26.10), `kn` v1.24.0, `tkn` v0.47.0, `tkn-pac` v0.54.0, `opc`
v1.25.0, `roxctl` 5.0.0 — with every checksum transcribed from a
vendor-published checksum file. Scanning those exact artifacts as a directory
(`evidence/runs/terminal-rebuild-projection-20261124.json`) gives
**3 Critical / 130 High** across the eight downloaded CLIs (`oc`, `kubectl`,
`kn`, `tkn`, `tkn-pac`, `opc`, `roxctl`, `helm`), and removes both containerd
Criticals outright: **`roxctl` 5.0.0 drops the
`github.com/containerd/containerd` dependency entirely**, so `GO-2026-5064` and
`GO-2026-5338` — previously written off as vendor-wait — simply disappear.
`helm` stays at v3.22.1: it already scans 0 Critical / 0 High and a v4
major-version change buys no security.

**The residual three are one advisory in three Red Hat binaries.** All three are
`GO-2026-6612` in `golang.org/x/net`, fixed only in v0.60.0: `oc` and `kubectl`
ship v0.56.0, `roxctl` v0.58.0. We cannot re-toolchain a Red Hat-built binary,
and the CLIs that do ship on current Go (`kn`, `tkn`, `tkn-pac`, `opc`) are
already at the newest upstream releases on go1.27.3 — and *still* carry fixable
High from stdlib advisories fixed only in go1.27.4 and from `x/net` v0.61.0
fixed only in v0.62.0. Upstream is simply ahead of every artifact we are allowed
to ship.

**Which is why a clean scan is unreachable — not why publishing is.**
`.github/workflows/terminal-release.yml` scans twice: `anchore/scan-action` with
`severity-cutoff: high` and `only-fixed: true` for the fixable inventory, then
`scripts/check_backend_staging_security.py` over the **unfiltered** report, which
blocks on every High/Critical/Unknown regardless of fix state. The projection
above carries 121 fixable High/Critical, and no combination of vendor artifacts
reaches zero: even the newest CLIs carry `GO-2026-6612` in `golang.org/x/net`
because upstream has not shipped a fixed release we are permitted to consume.

Until `27a1ede0` that made the publish path dead code rather than a red
pipeline. The gate now accepts a `launchpad/risk-acceptance/v1` record and
subtracts only what the record enumerates, by exact
`(advisory, package, severity)` triple, bound to the component, the released
revision, and either the candidate digest or an explicit `digest_pending`. A
scanner suppression can never be covered, an unlisted finding still blocks, the
record expires within 180 days, unknown fields are rejected, and
`platform_staging_qualified` stays `false`. The fixable-only step is evidence
now (`fail-build: false`), so the Python gate is the single decision, and
`scripts/render_risk_acceptance.py` transcribes a measured report into the
record and refuses to write one the gate would reject.

Verified against the deployed digest: the 1254 blocking matches collapse to
**376 triples**, the gate reports `PASS-SCAN-ONLY` / `risk_acceptance: GRANTED`
/ `gate_basis: SIGNED-ACCEPTANCE`; one fabricated extra advisory still blocks as
`APPLIED-INCOMPLETE`; a tampered digest exits 2 as `INVALID`. That run is
retained as `evidence/runs/risk-acceptance-mechanism-proof-20261124.json`, which
states in the file itself that it is a mechanism proof signed with a placeholder
and authorises nothing.

**Two things that made the publish path unreachable, not just red.** First,
`terminal-release.yml` has never existed on `main` in either `rhpds/launchpad` or
the fork, and GitHub only registers `workflow_dispatch` for workflows on the
default branch — the dispatch API returns `HTTP 404: workflow
terminal-release.yml not found on the default branch`. So no terminal release
was ever dispatched, and no run ever failed: the path was undiscoverable. Second,
the gate runs *before* the push, so at decision time the candidate lives only in
the runner's docker store. Measured on a single image, three values disagree:
`podman .Id` `b24e8f7b…`, stored `RepoDigests` `91aae7d5…`, grype
`manifestDigest` `ef6af63b…`. A `candidate_digest` read from CI would have been a
phantom, which is why the acceptance path needs `digest_pending` when no real
digest exists.

**That gap then failed a real run, which is how the rest of it was found.**
Dispatch was impossible until the workflow existed on the default branch, so
registration came first (`14b13d0e`, one additive file on `rhpds/main`). The
first measurement run then failed at the gate with **exit 2 / `INVALID` —
"Scan does not match the candidate image"** on a candidate that matched
perfectly (`45713500003`). The runner uses the containerd image store
(`driver-type: io.containerd.snapshotter.v1`), where `docker image inspect .Id`
is the *manifest* digest, while grype reports the *config* digest
(`sha256:b72689ac…`). The gate compared the two. buildx does not help: its
`imageid` output is the iidfile, which on that store is the manifest digest
(`sha256:ceafb199…`), and its metadata output carries only
`containerimage.digest`. So **no independent config digest exists before the
push**, and grype's manifest digest cannot substitute because loading
re-serialises the manifest (`763cfca7…`).

The consequence is a division of proof, now explicit in both workflows and
tested. The gate binds the report to the tag it scanned (`userInput`) and takes
the candidate identity from the report's own `source.target.imageID`. The
*publish* step then proves the binding before cosign signs anything: it reads
the manifest the registry actually serves with
`docker buildx imagetools inspect --raw`, and fails unless its `config.digest`
equals the config digest the scan recorded; the receipt records both `image_id`
and `manifest_digest`. That pair is sound — a report about any other image
passes the gate and then fails at publication. `backend-release.yml` had the
identical defect and received the identical fix; its "working publish history"
did not protect it, because a working run under the classic store hides a check
that is wrong under the containerd store.

**A signed record cannot live in the revision it names.** `validate_acceptance`
requires `source_revision` to equal the revision being released, and the gate
read the record from the checked-out tree. A commit cannot contain a file naming
its own SHA — committing the record changes the SHA it names — so exact equality
plus in-tree lookup is unsatisfiable, and no dispatch could ever have applied a
committed record. The record now lives one commit later, on the workflow
revision, and the gate materialises it with `git show "$WORKFLOW_SHA:$path"`,
still binding it to `EXPECTED_SHA` and refusing an empty record. The reviewed
bytes are copied to `staging-risk-acceptance.yaml` and uploaded with the rest of
the decision evidence, so the exact record is auditable even though it is not in
the released tree.

The two-build path that remains is honest but not free. Because
`Containerfile:35` runs `dnf -y --refresh upgrade`, the image is not
reproducible, so the acceptance must be rendered from the report of a build whose
RPM inventory the release build reproduces. If the release build pulls a newer
RPM, its extra findings are unlisted, and the gate blocks — correctly. In that
case the honest move is to render again from the release build's own retained
report and sign again; there is no mechanism here that lets a stale acceptance
widen its own scope.

**The record was then signed, and it is deliberately unflattering.** It lives at
`evidence/security/terminal-risk-acceptance-20261125.json` (with a `.sha256`
sibling), names revision `e26a87c3`, and enumerates **68
`(advisory, package, severity)` triples** — 59 advisories across 27 packages,
covering 179 High, 3 Critical and 8 Unknown matches. The three Criticals are one
advisory, `GO-2026-6612` in `golang.org/x/net`, inside the shipped `oc`,
`kubectl` and `roxctl`. 39 advisories are Go modules baked into vendor CLIs and
20 are UBI RPMs the repository reports `not-fixed` or `wont-fix`.

Two properties of that record are worth stating plainly. First, its scope was
transcribed mechanically from a measured report
(`report_sha256 983befb8…`, build of `66c82756`), not by hand, and
`report_sha256` is audit metadata rather than a binding: the gate's binding is
the exhaustive enumeration, so a *newer* advisory that the release build picks up
is simply not on the list and blocks. Second, the measured revision is
`66c82756`, while the record names `e26a87c3`; between those two commits the
terminal build context is byte-identical (`git diff 66c82756 e26a87c3 --
workshop-images/showroom-terminal/` is empty), so the measurement applies to the
revision being released. That is a claim about the build *inputs*, and it was
checked rather than assumed.

The record was exercised against the gate before dispatch: with it the gate
returns `PASS-SCAN-ONLY` / `risk_acceptance: GRANTED` /
`gate_basis: SIGNED-ACCEPTANCE` and zero unaccepted findings; deleting one
accepted entry returns `BLOCKED` / `APPLIED-INCOMPLETE`; and naming a different
revision returns `INVALID` (exit 2). So the signature subtracts exactly the
enumerated triples and nothing else.

So the decision is now about cost, not feasibility. Three honest options:
(a) publish with a signed applicability review covering the residual 3 and the
RPM tail, routed through that mechanism — mechanical, and the only option that
reduces participant exposure; (b) drop `oc`, `kubectl` and `roxctl` and accept a
terminal without cluster-admin tooling, which changes what labs can teach; or
(c) leave the terminal unpublished and keep `324dc5c4` serving, which is a
choice to keep shipping 112 Criticals. Option (a) needs an owner signature, and —
because Brief 1 is scoped to the two backend binaries and explicitly excludes
`skopeo` — it needs a terminal-scoped acceptance of its own rather than Brief 1.

**Option (a) was taken, and it landed.** The owner signed a
`launchpad/risk-acceptance/v1` record for the terminal — 68 enumerated triples,
90 days, expiring 2027-02-23 — and the release workflow then ran green at
`e26a87c3` (run `45721636396`, dispatched from workflow revision `cb7c8839`).
The result is a signed, attested
`ghcr.io/rhpds/launchpad-showroom-terminal@sha256:548b0e3c…`. The gate reported
`PASS-SCAN-ONLY` / `GRANTED` / `SIGNED-ACCEPTANCE` with 68 of 68 accepted entries
matched and none unused, and the release build reproduced the measured inventory
*exactly* — the same 68 triples, no new advisory. That last point is what makes
the record usable: the build is not reproducible, and only the enumeration, not
a digest comparison, carries the acceptance.

Promotion took the first option above. `skopeo copy --all` into
`quay.io/rh-ee-jkershaw/launchpad-showroom-terminal:git-e26a87c3` preserved the
manifest digest (`548b0e3c…`) and the config digest the gate had verified
(`6a098f27…`), so the Quay tag is the same artifact the signature covers; the
GHCR package that "does not exist yet" above now does. Cosign verifies at GHCR
(identity `terminal-release.yml@refs/heads/codex/flightpath-migration-20260922`,
Rekor `logIndex 4113914419`). The signature does not travel with the copy, which
is exactly why the runbook makes digest equality the load-bearing step.

Four files were repinned (`ae61cb4d`) and the live `launchpad-cluster-targets`
differed from the render in exactly one line — the digest. One trap is worth
recording because it was real: `oc apply` followed by `oc rollout status`
reported success while the 22-hour-old backend pod kept mounting the old digest.
A ConfigMap is not part of the pod template, so nothing restarted, and the
adapter reads cluster targets at startup. `oc rollout restart deploy/backend`
took generation 382 → 383, and the new pod mounted `548b0e3c…`. Evidence:
`evidence/runs/terminal-promotion-20261125.json`.

**The image is closed; the participant proof is not.** With the digest live and
pinned, a real one-seat `public_code` order against `virtualization-ai-201` was
placed through `POST /api/v1/workshops/orders` and **failed closed on capacity**,
not on the image:

```
Requested 1 seats but cluster supports 0 (CPU: 0, Memory: 265, Pods: 20; Eligible nodes: 3)
```

The three eligible workers (`fp1`–`fp3`) carry 681 784 m of CPU requests against
a 606 912 m budget — 80 % of 758 640 m allocatable, which is the
`WORKSHOP_CAPACITY_HEADROOM_PCT` reserve. The seat needs 625 m, so admitting it
requires freeing at least 75 497 m of requests or lowering the reserve. The
demand is not Launchpad's: `ols-eval-models` alone requests 301 cores,
`cpd-instance-1` 102, `llm-bench` 74, `cascade-compression` 36, and Launchpad's
own model endpoints in `launchpad-model-candidate` account for 110.

The order still behaved correctly: it was created `failed` with a `pending` seat,
no namespace, no session and no terminal pod, so the failure mode is fail-closed
rather than half-provisioned.

**The seat proof now passes, and it took two attempts and one more trap.** The
capacity block cleared the next day for a reason outside Launchpad:
`ols-eval-models` released its `granite-v3` (128 cores) and `deepseek-v4-flash`
(44 cores) pods, dropping requests on `fp1`–`fp3` from 681 784 m to 509 784 m —
exactly 172 000 m. At the untouched 20 % reserve that admits 20 seats, so the
temporary 10 % headroom window that had been applied to make room was reverted
before any order was placed, with the pod-spec env fingerprint byte-identical to
its pre-change value. No seat in this record was admitted under weakened policy.

The first real order then failed a different test, and this one matters more than
the capacity numbers. It came up `ready` — and its terminal pulled
`324dc5c4…`, the **previous** digest. The ConfigMap was correct, the backend's
mounted `clusters.yaml` was correct, and the `lifecycle-worker`'s own mounted
file was correct; but the worker process had been up since 2026-11-25T00:56Z and
held cluster targets in memory from before the pin. The backend rollout never
touched it, so the showroom Application it rendered carried the old digest. After
`oc rollout restart deploy/lifecycle-worker` (and confirming no pre-pin worker
remained — the rollout reported success while the old pod was still `Running`
with a `deletionTimestamp`), a second order came up `ready` with the `terminal`
container's image **and** `imageID` both `548b0e3c…`.

Both seats were reclaimed to `completed`, with their namespaces deleted and no
terminal pods left behind. Evidence:
`evidence/runs/terminal-participant-seat-20261126.json`, which supersedes the
`BLOCKED-ON-CAPACITY` status in the 2026-11-25 record without editing it — that
status was true when it was written.

**What is still not guaranteed is admission.** The cluster can now admit a seat
because another team stopped requesting 172 cores, not because Launchpad gained
capacity, and nothing prevents those pods returning. The terminal image, its
signature, the pin, and the participant pull are all proven; a later order can
still fail closed on CPU, and that will remain a scheduling answer rather than an
image answer.

**Why this outranks every other Track B item.** 16 catalog items declare
`showroom_terminal_storage`. The terminal is not one blocked experience; it is
the substrate under nearly all showroom-backed orderability, so no seat-cap or
exposure change unblocks external participant orders while this is unresolved.

**The publish target is a second, independent decision.** A green run today
pushes to `ghcr.io/rhpds/launchpad-showroom-terminal`, which does not exist yet
(`gh api` returns 404), while both Flightpath overlays pin
`quay.io/rh-ee-jkershaw/launchpad-showroom-terminal@sha256:324dc5c4…`. Signing a
digest the cluster never pulls would be theatre, so the promotion path has to be
chosen before any dispatch. What the live cluster actually does:

| Workload | Image | Pull secret |
|---|---|---|
| `backend`, `lifecycle-worker` | `ghcr.io/jkershawrh/…-candidate@sha256:3bedbc0c…` | `launchpad-backend-ghcr-pull`, `launchpad-registry-pull` |
| `public-access-gateway` | `ghcr.io/rhpds/launchpad-backend-flightpath@sha256:298527ff…` | `launchpad-registry-pull` |
| `cloudflare-tunnel` | `ghcr.io/rhpds/launchpad-backend@sha256:6af8015c…` | none — package is public |
| showroom seats | `quay.io/rh-ee-jkershaw/launchpad-showroom-terminal@sha256:324dc5c4…` | none — public Quay |

So "GHCR is not this cluster's registry" is false; GHCR already serves the
control plane from both `rhpds` and the fork. The objection is narrower and sits
in the provisioner: `_requires_image_pull_grant`
(`backend/app/adapters/openshift/provisioning.py:1502`) declines to bind an
internal pull grant only when every showroom support image matches
`quay\.io/…@sha256:…` via its local `pinned_quay()` helper. Point the terminal at
GHCR and the adapter starts creating a `partner-ai-launchpad` RoleBinding for a
registry the image does not come from, and
`test_deployed_cluster_images_and_pilot_catalog_preserve_grant_boundary`
(`backend/tests/test_openshift_image_pull_grant.py:47`, which reads the live
overlay and expects `flightpath_grant: False`) fails. That test is the invariant,
not an inconvenience.

`config/artifact-registry-policy.yaml` points a third way: it names
`quay.io/redhat-gpte` as the authoritative origin, records
`organization_ownership_approved: false`, and marks every
`pull_grant_verified: false`. Its gate (`scripts/validate_artifact_registry.py`,
run from CI) requires each repository to sit under that origin, so it cannot be
used to bless GHCR either. The deployed `rh-ee-jkershaw` namespace is a personal
pilot path that satisfies neither the policy nor the grant boundary.

Two coherent choices, with different costs:

* **Keep Quay and promote into it.** Build and sign in GHCR, then copy the
  digest into the Quay repository the overlays already pin. Preserves
  `pinned_quay`, the grant boundary, its test, the policy, and every existing
  reference; because the acceptance binds to the digest, the copy is auditable.
  Costs a promotion step plus a Quay robot token as a repository secret — CI
  holds no Quay credential today — and the overlays need only a digest edit.
* **Move the showroom images to GHCR.** Needs a deliberate widening of the grant
  boundary (generalize `pinned_quay` into an allowlist of immutable
  control-plane registries), a pull secret or public package for every seat
  namespace, an update to the registry policy, and edits to the three tests that
  pin today's behaviour. Larger, and it changes the code whose job is to decide
  when to stop granting blanket pull.

The first is recommended: it moves no security invariant, changes no trust path,
and repins three files. It also matches how `324dc5c4` reached Quay.

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
