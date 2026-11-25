# Phase 0 owner decisions — GO-2026-5932 disposition and Console cutover window

Status: OPEN — Brief 1 awaits one reviewer signature; Brief 2's second
signature was waived 2026-11-24 (§2.11). Neither item is a code change.
Date: 2026-11-24.
Branch: `codex/flightpath-migration-20260922`.
Decision owners: Launchpad owner (`jkershaw`, both briefs); Launchpad platform
security reviewer (`jkershaw`, Brief 1 — identity confirmed 2026-11-24);
Flightpath/network owner (**sign-off waived for Brief 2, §2.11**).
Source of the gate: `docs/staging-candidate-order-of-operations-20261016.md`,
Phase 0, items 1 and 2. Restated as "open, blocking" in
`docs/flightpath-orderable-capacity-and-roadmap-20261124.md`, Track A, Phase 0.

This document exists to be signed. It contains exactly two briefs. Each ends
with a decision line that names the option, the record to file, and the
condition under which the decision lapses. Nothing here authorises a cluster
mutation; Brief 2 is a window plan that still requires a separate go-ahead at
execution time.

## Decision summary

| # | Item | Recommended decision | Record to file | Blocks |
|---|---|---|---|---|
| 1 | `x/crypto` GO-2026-5932 (2 unrated backend matches) | Accept with scope, as a signed advisory-review disposition — **not** a scanner ignore | `evidence/convergence/backend-openpgp-advisory-disposition-20261124.yaml` | Backend security gate, which gates the immutable candidate image |
| 2 | Console / `labs.smg-helix.ai` collision | Native-route cutover (remove the operator `spec.route` override), not a new DNS hostname | `evidence/convergence/flightpath-console-cutover-<date>.yaml` produced by the window | Track A Phase 4; full participant journey |

Both are cheap relative to the work they unblock, and both are reversible or
time-bounded. Neither requires a catalog, seat-ceiling, or image change.

---

# Brief 1 — `x/crypto` GO-2026-5932 disposition

## 1.1 What the advisory is, in plain terms

`GO-2026-5932` is a Go vulnerability database entry for
`golang.org/x/crypto/openpgp` and its subpackages. It is **not** a memory-safety
or remote-code-execution bug with a patch. It is a "package unsafe by design"
deprecation notice: the `openpgp` packages are frozen, receive no security
fixes, and are documented as unmaintained. The advisory's own guidance is to
stop using them and, where OpenPGP interoperability is genuinely required, move
to the maintained ProtonMail fork.

Checked against the upstream record on 2026-11-24
(`https://vuln.go.dev/ID/GO-2026-5932.json`):

| Field | Value | Consequence here |
|---|---|---|
| Status | `REVIEWED` | It is a real, triaged entry, not a stale placeholder |
| Published / modified | 2026-07-07 / 2026-11-02 | Actively maintained entry; will keep reappearing in scans |
| CVE / CVSS | none / none | No severity to compare against a High threshold; the gate treats it as `Unknown` |
| Fix event, `golang.org/x/crypto` | `0.58.1-0.20261009181718-2f1f834330b2` | A pseudo-version that only exists because of the carve-out below |
| Fix event, `golang.org/x/crypto/openpgp` | present, **no fixed version** | This is the binding constraint |

The gate consequence is mechanical. `scripts/check_backend_staging_security.py`
blocks on any `High`, `Critical`, **or `Unknown`** match, and it checks the
suppressed inventory as well as the counted inventory:

```python
blocked = any(
    ...
    for inventory in (counts, suppressed)
    for severity in ("High", "Critical", "Unknown")
)
```

That detail matters for the decision. A scanner ignore or a suppression entry
does **not** clear this gate — suppressed `Unknown` matches are part of the
blocking condition. There is no allowlist in the script. So the only honest
path is a documented, scoped, human-signed disposition, which is what the
order-of-operations document already says is required.

Current evidence: `evidence/convergence/backend-security-95fec905-20261015.yaml`
records `unrated: 2`, `suppressed_high_critical_unrated: 0`,
`risk_acceptance: NOT-GRANTED`, `scanner_ignore_added: false`. The two matches
are grouped as `golang.org/x/crypto: two unrated matches requiring
advisory-specific review`.

## 1.2 Where the code is in this repo

The import is not in Launchpad's own Go code. It enters through the `oc` binary
that the backend image builds and ships.

| Location | What it shows |
|---|---|
| `backend/Containerfile` line 69 | `go test ... -tags containers_image_openpgp ... github.com/containers/image/v5/signature` |
| `backend/Containerfile` lines 73 and 78 | `go build ... -tags "include_gcs include_oss containers_image_openpgp" ... ./cmd/oc` |
| `backend/Containerfile` line 149 | built `oc` copied into the runtime image at `/usr/local/bin/oc` (helm at line 150) |

The `containers_image_openpgp` build tag is what selects the pure-Go
`x/crypto/openpgp` implementation inside `containers/image/v5/signature`
instead of the cgo/`gpgme` path. Removing the tag is therefore not a one-line
change: it makes the build require cgo plus system `gpgme`, or a Rust/sequoia
stack. The pinned build also asserts the compiled module closure explicitly
(`compiled-module-closure.txt`, and a hard `exit 1` if
`github.com/docker/docker` appears), which is why this dependency was a
deliberate, reviewed choice rather than an accident.

**A second importer exists, and the brief originally missed it.**
`workshop-images/showroom-terminal/Containerfile` builds `skopeo` from source
with the same tag (lines 17 and 19) and installs it at `/usr/bin/skopeo` for
learners. `evidence/convergence/image-remediation-20261020.yaml` records
`skopeo_unrated: [GO-2026-5932]` in the terminal image after the grpc fix. So
the advisory ships in **both** images.

The reachability argument does not transfer. `oc` is an operator-internal
helper invoked on two resource paths; `skopeo` is a participant-invocable CLI
in the terminal image, where signature verification is a supported verb. The
backend disposition is therefore correct as scoped — it explicitly excludes
other images — but it leaves a real terminal finding standing, and that one
cannot borrow the `oc` reachability story.

## 1.3 Why this cannot be fixed by upgrading

Three separate attempts fail, and the repo already contains the evidence for
each:

1. **Bump `golang.org/x/crypto`.** As of `golang.org/x/crypto v0.59.0`
   (2026-11-11), the parent module no longer ships `openpgp`; the package was
   carved out into its own module, `golang.org/x/crypto/openpgp
   v0.1.0-deprecated` (tag `refs/tags/openpgp/v0.1.0-deprecated`). That module
   carries the advisory range with **no fixed version**. A bump therefore does
   not remove the finding — it relocates it from the parent module to the
   submodule and keeps the same unmaintained code linked into `oc`. This is the
   substance of `not_a_patch_version_fix` in
   `evidence/convergence/image-remediation-20261020.yaml`.
2. **Migrate to the maintained fork.** `github.com/ProtonMail/go-crypto
   v1.4.1` was tried on disposable module copies
   (`evidence/convergence/openpgp-compatibility-experiment-20261020.yaml`).
   All three focused upstream compatibility tests fail **3/3** on
   `fixtures/invalid-blob.signature-v3` with "LiteralData not followed by
   signature". The experiment was rejected with `security_waiver: false`; the
   open question (are legacy v3 signatures an intended supported input?) is a
   product question, not a build fix.
3. **Block until upstream ships a fix.** There is no fix to wait for. The
   "fixed" event on the parent module is a carve-out, not a repair, and the
   openpgp module is explicitly deprecated with no fix version. Blocking is
   indefinite by construction.

## 1.4 Reachability — the basis for scoped acceptance

The code is *linked* but not *reachable* from Launchpad's call paths. The
backend invokes `oc` for resource operations only — `oc get` and
`oc create route` — never `oc image`, `oc build`, or image-signature
verification. No Launchpad code path calls GPG or signature verification.
This is the same usage boundary recorded for the client advisory review
(`evidence/convergence/backend-remaining-security-disposition-20261014.yaml`:
`observed_backend_operations: [get-resources, create-edge-route,
apply-manifests, kustomize-apply]`, `absent_direct_calls: ... oc build or oc
image`).

The honest caveat: reachability is argued from the call sites reviewed, not
from a dynamic taint proof. The disposition must say so, and must name the
condition that would invalidate it.

## 1.5 Options and staging-gate consequences

| Option | What it costs | Effect on the staging gate | Verdict |
|---|---|---|---|
| **A. Accept with scope** (signed advisory-review disposition) | One record, one reviewer signature, 90-day review | Unblocks the two backend `Unknown` matches *for this scope and expiry*; the terminal `skopeo` finding is out of scope and stays open; the gate still blocks on all other High findings | **Recommended** |
| B. Scanner ignore / suppression | One config change | **Does not work.** The gate blocks suppressed `Unknown` too; would also be a silent waiver, which the repo's own rules forbid | Rejected |
| C. Bump `x/crypto` | Rebuild, re-pin, re-scan | Moves the finding to `x/crypto/openpgp v0.1.0-deprecated`; still `Unknown`; no fixed version | Rejected as a fix (may be worth doing for other reasons) |
| D. ProtonMail fork migration | Patch `containers/image`, resolve v3-signature policy | Would remove the finding, but breaks v3 signature fixtures 3/3 and needs a product decision on legacy input | Deferred, not rejected forever |
| E. Drop `containers_image_openpgp` | cgo + `gpgme` or Rust/sequoia in the image | Removes the finding; adds native toolchain, image size, and a new supply chain | Rejected for staging timeline |
| F. Block | Nothing | Gate stays red indefinitely; no upstream fix exists | Rejected |

Option A is the only option that is both honest and finite. It does not claim
the code is safe; it records that the code is unreachable from Launchpad's
call paths, that no fix exists, and that the acceptance expires.

## 1.6 Exact record to file

Create `evidence/convergence/backend-openpgp-advisory-disposition-20261124.yaml`
(note: this brief does not create it — the reviewer signs it). Schema
`launchpad/advisory-disposition/v1`, matching the style already used by
`evidence/convergence/backend-remaining-security-disposition-20261014.yaml`.

Required fields:

| Field | Value / requirement |
|---|---|
| `schema` | `launchpad/advisory-disposition/v1` |
| `date` | Signature date |
| `status` | `ACCEPTED-WITH-SCOPE` |
| `advisory` | `GO-2026-5932`, with the `vuln.go.dev` URL |
| `advisory_status_at_review` | `REVIEWED`; modified date observed |
| `cve` / `cvss` | `none` / `none` — state explicitly that no severity exists |
| `affected_modules` | `golang.org/x/crypto` (findings 2) and, if present, `golang.org/x/crypto/openpgp v0.1.0-deprecated` |
| `scanner_source` | `95fec905f1c2a3b6581de5e290f711af2ede37c1`, run URL, `unrated: 2` |
| `candidate_digest` | The digest this disposition covers — acceptance is per-image, not global |
| `build_tag_basis` | `containers_image_openpgp` in `backend/Containerfile`; `oc` at `/usr/local/bin/oc` |
| `fixed_version_available` | `false`, with the carve-out explanation |
| `upgrade_attempts` | Parent bump (relocates), ProtonMail fork (3/3 v3 failures), tag removal (cgo/gpgme) |
| `reachability` | Reviewed call sites; `oc get` / `oc create route` only; `reachability_proven: false` stated as a limitation |
| `scope_statement` | Verbatim block below |
| `residual_risk` | Verbatim block below |
| `owner_role` | `launchpad-platform-security-reviewer` |
| `owner_signature` | Name + date |
| `expires` | `2027-02-22` (90 days) |
| `reopen_triggers` | List in §1.9 |
| `scanner_ignore_added` | `false` |
| `live_changes` | `false` |

Skeleton:

```yaml
schema: launchpad/advisory-disposition/v1
date: '2026-11-24'
status: ACCEPTED-WITH-SCOPE
advisory: https://vuln.go.dev/ID/GO-2026-5932.json
advisory_id: GO-2026-5932
advisory_status_at_review: REVIEWED
advisory_modified_at_review: '2026-11-02'
cve: none
cvss: none
severity_basis: >-
  The entry carries no CVE and no CVSS. The staging gate blocks it because the
  scanner reports it as Unknown, not because it scores High or Critical.
affected_modules:
  - {module: golang.org/x/crypto, matches: 2}
build_tag_basis:
  tag: containers_image_openpgp
  containerfile: backend/Containerfile
  linked_binary: /usr/local/bin/oc
  binary_copied_at_containerfile_line: 149
scanner_source:
  commit: 95fec905f1c2a3b6581de5e290f711af2ede37c1
  run: https://github.com/jkershawrh/intel-ai-launchpad/actions/runs/38758481803
  unrated_matches: 2
  retained_artifact: backend-vulnerability-scan-95fec905f1c2a3b6581de5e290f711af2ede37c1
candidate_digest: sha256:d222ed9ae801475224b1f793e5f758ab9d31f83c0be01aee5978e88b66a83f69
fixed_version_available: false
fixed_version_reason: >-
  golang.org/x/crypto v0.59.0 removed the openpgp package. The replacement
  module golang.org/x/crypto/openpgp v0.1.0-deprecated is deprecated and its
  advisory range has no fixed version. Upgrading relocates the finding; it does
  not remove it.
upgrade_attempts:
  parent_module_bump: RELOCATES-NOT-REMOVES
  protonmail_fork: REJECTED-3-OF-3-V3-SIGNATURE-FIXTURES-FAIL
  remove_build_tag: REQUIRES-CGO-GPGME-OR-RUST-SEQUOIA
reachability:
  reviewed_call_sites: [oc get, oc create route]
  absent_calls: [oc image, oc build, image signature verification]
  reachability_proven: false
  limitation: Static review of call sites, not a dynamic taint proof.
scope_statement: |
  This disposition covers the two unrated GO-2026-5932 matches in the
  containers_image_openpgp build of /usr/local/bin/oc shipped in the backend
  image at the recorded candidate digest, and nothing else. It does not
  disposition any other High, Critical, or Unknown finding, any other image,
  any other build tag, or any future code path that verifies OpenPGP
  signatures, calls oc image, or calls oc build. In particular it does not
  cover the GO-2026-5932 finding in /usr/bin/skopeo in the showroom-terminal
  image, which requires its own disposition and its own reachability
  argument. It is not a scanner suppression and does not change any scanner
  configuration.
residual_risk: |
  The unmaintained openpgp code remains linked into the shipped oc binary for
  the life of the acceptance. If a future Launchpad feature routes untrusted
  image signatures through oc, or enables oc image / oc build, this
  disposition no longer applies and must be reopened before that feature
  ships. The scanner will keep reporting the finding on every rebuild; the
  report is expected, not a regression. There is no upstream fix to wait for.
owner_role: launchpad-platform-security-reviewer
owner_signature: null   # name + date at signing
expires: '2027-02-22'
reopen_triggers:
  - Any Launchpad code path starts verifying OpenPGP signatures.
  - oc image or oc build becomes reachable from backend request handling.
  - A CVE is assigned to GO-2026-5932.
  - Upstream publishes a fixed openpgp module version.
  - The candidate digest changes without re-review.
scanner_ignore_added: false
suppression_added: false
live_changes: false
staging_qualified_by_this_record: false
```

## 1.7 Residual risk if accepted

| Risk | Likelihood | Impact | Handling |
|---|---|---|---|
| Unmaintained code later reachable via a new feature | Low | High | Reopen trigger 1; feature review must check this |
| Reader treats "accepted" as "safe" | Medium | Medium | `scope_statement` and `residual_risk` are verbatim in the record |
| Finding misread as a regression on the next scan | High | Low | Record states the scanner will keep reporting it |
| Scope drifts to other unrated/High findings | Medium | High | Scope names the exact digest and module; everything else stays blocked |
| Expiry passes unnoticed | Medium | Medium | Expiry is a field; the 90-day date is on the decision line |

This acceptance does not make the image safe. It makes the gate's question
answerable: the finding is known, has no fix, is unreachable today, and lapses
in 90 days.

## 1.8 What must be confirmed before signing

Two things are not verifiable from the repo as it stands:

1. **Why there are two matches.** The working assumption is that one advisory
   is counted twice — once for the parent module and once for the openpgp
   import path. The retained scan JSON is not in this repository (it lives in
   the `backend-vulnerability-scan-95fec905...` CI artifact). Confirm the two
   match IDs in that artifact before signing. If they are *different*
   advisories, this disposition is incomplete.
2. **That no other code path pulls in openpgp — answered, and it did.** The
   `oc` build is one path; the showroom-terminal image's `skopeo` is a second.
   The reviewer must either accept that the terminal finding remains open or
   extend this brief into a two-image decision. Do not sign on the assumption
   that `oc` is the only importer.

## 1.9 Decision line — Brief 1

> **Decision 1:** Accept GO-2026-5932 with scope. File
> `evidence/convergence/backend-openpgp-advisory-disposition-20261124.yaml`,
> schema `launchpad/advisory-disposition/v1`, status `ACCEPTED-WITH-SCOPE`,
> covering the two unrated matches in the `containers_image_openpgp` build of
> `oc` at candidate digest
> `sha256:d222ed9ae801475224b1f793e5f758ab9d31f83c0be01aee5978e88b66a83f69`.
> This is an advisory-review disposition, not a scanner suppression. It expires
> 2027-02-22 and reopens on any of the listed triggers.
>
> Approved by: J Kershaw — `launchpad-platform-security-reviewer`, identity
> confirmed 2026-11-24
> Date: __________ **not yet executed** — the match IDs in §1.8 item 1 are still
> unconfirmed, and this disposition is per-image-digest, so a signature taken
> before that check would cover a build nobody can identify later.

---

# Brief 2 — Console hostname cutover window

## 2.1 The collision, as derived from repo evidence

`labs.smg-helix.ai` is asked to be two different things: the participant
Launchpad origin and the OpenShift Console origin. Because the Console
operator owns that hostname, a participant hitting the Console path is
redirected into Console instead of Launchpad, and vice versa.

From `evidence/convergence/flightpath-staging-readonly-preflight-20261014.yaml`
(read-only preflight; `mutation_performed: false`):

| Object | Observed value | Why it collides |
|---|---|---|
| Console operator canonical hostname | `labs.smg-helix.ai` | Same host as the participant origin |
| Console operator TLS secret | `launchpad-public-console-tls` | Serves the participant-named cert for Console |
| Native Route `openshift-console/console` | backend `console-redirect` | Native Console traffic lands on the redirect service |
| Custom Route `openshift-console/console-custom` | backend `console` on the labs host | Participant-named Console endpoint |
| Console OAuthClient callback | `https://labs.smg-helix.ai/auth/callback` | Console login returns to the shared host |
| Tunnel `OPENSHIFT_CONSOLE_UPSTREAM_HOST` | `labs.smg-helix.ai` (pre-repair) | Proxy forwards Console to the shared host |
| Backend cluster target | `public_console_url: https://labs.smg-helix.ai` | `deploy/launchpad/overlays/flightpath-candidate/candidate-clusters.yaml` |

The checked-in tunnel deployment has already been updated to the native host:

```
OPENSHIFT_CONSOLE_HOST        = console-openshift-console.apps.flightpath.fm2aihpcsed.com
OPENSHIFT_CONSOLE_UPSTREAM_HOST = console-openshift-console.apps.flightpath.fm2aihpcsed.com
OPENSHIFT_CONSOLE_CALLBACK_URL  = https://console-openshift-console.apps.flightpath.fm2aihpcsed.com/auth/callback
```

(`deploy/tunnel-oncluster/flightpath-deployment.yaml` lines 79–81.) The router
is path-based on a single host and dispatches with `_select_upstream` and
rewrites with `_rewrite_url` (`deploy/tunnel-oncluster/router.py`), so the
participant host can keep serving Launchpad while Console traffic is steered to
the native upstream.

**What the repo does not contain.** The Console operator object itself
(`console.operator.openshift.io/cluster`) is a live cluster object; there is no
checked-in manifest for it. The only repo artifact is the merge patch,
`deploy/console-embed/flightpath-native-route.patch.json`:

```json
{ "spec": { "route": null } }
```

So the precise current value of `spec.route` must be read live. The collision
above is derived from the October preflight evidence, not from a manifest in
this tree.

## 2.2 Unverified state — read this before scheduling

There is a direct contradiction in the repo and it must be resolved by a live
read, not by picking a side:

- `evidence/convergence/flightpath-native-console-repair-20261014.yaml` says
  the native-route repair was **deployed** (`owner_approved_cutover: true`,
  `deployed_result.canonical_console` = native host, Console operator
  `Available: true, Degraded: false`) and browser-verified.
- `docs/flightpath-console-access-separation.md` (same date) states the repair
  is "approved and deployed".
- But `docs/staging-candidate-order-of-operations-20261016.md` (two days later)
  still lists the cutover window as an open Phase 0 decision, and
  `docs/flightpath-orderable-capacity-and-roadmap-20261124.md` still shows
  Phase 0 open and Phase 4 "Console cutover ... not started".

Both cannot be true. The platform has also been scaled to zero since
2026-11-16 (all Deployments `0/0`, CronJobs suspended, routes 503,
`labs.smg-helix.ai` 530, no Argo CD apps), so nothing can be checked right now.

The window therefore opens with **Step 0, a read-only object check**, and
branches:

| Live finding | Meaning | Action |
|---|---|---|
| `spec.route` is absent/null and native host + callback are live | The October repair is still in place | No cutover. Verify only; record and close Phase 0 item 2 |
| `spec.route.hostname: labs.smg-helix.ai` still set | The repair was reverted or never persisted | Run the cutover below |
| Anything else | Unknown state | Stop. Capture, escalate, do not mutate |

Do not assert either world in the record until Step 0 returns.

## 2.3 What the cutover changes

| Change | Object | Detail |
|---|---|---|
| Remove the custom route override | `console.operator.openshift.io/cluster` | Apply `{"spec":{"route":null}}` from the checked-in patch; let the operator reconcile the native host and native `/auth/callback` |
| Point the tunnel at the native upstream | `deploy/tunnel-oncluster/flightpath-deployment.yaml` | Already checked in (lines 79–81); confirm deployed env matches, then roll the tunnel |
| Keep the participant host | `labs.smg-helix.ai` / router | Unchanged; router continues to serve Launchpad and translate Console callbacks back to the participant origin |

Explicitly **unchanged**: Keycloak issuer, participant hostname and existing
lab links, namespace RBAC, catalog pins, backend and worker images, Console
operator replicas. This list is the same one recorded in the repair evidence
under `unchanged:`.

Do not apply the patch from a broad platform overlay. It is intentionally not
auto-applied; it is applied only to a verified Flightpath connection in the
approved window.

## 2.4 Rollback procedure

Rollback restores the pre-cutover Console routing without touching participant
identity or data.

| Step | Action | Verify |
|---|---|---|
| R1 | Re-apply the captured `spec.route` block (`hostname: labs.smg-helix.ai`, secret `launchpad-public-console-tls`) to the Console operator | Operator reports `Progressing: false, Degraded: false`; `spec.route.hostname` reads back |
| R2 | Confirm `openshift-console/console-custom` exists and targets `console` | Route present; backend `console` |
| R3 | Restore the tunnel Console upstream env to the captured pre-cutover value | Deployed env matches capture |
| R4 | Roll the tunnel pods | `cloudflare_tunnel` and `public_access_gateway` ready |
| R5 | Re-run the browser checks | Pre-cutover behaviour returns (the redirect symptom is expected and is the success signal for rollback) |
| R6 | Record the rollback in the window record with timestamps | Rollback section populated |

Rollback trigger: any acceptance criterion in §2.8 fails and is not fixed
within 20 minutes, or the Console operator enters `Degraded: true`.

## 2.5 What "rollback capture" records

The capture is taken **before** any mutation and is the input to R1–R5. It is
stored with the window record and hashed; secret *values* are never exported.

| Item | Captured as |
|---|---|
| `console.operator.openshift.io/cluster` | Full YAML, secret references by name only |
| `openshift-console/console` and `console-custom` Routes | Full YAML |
| Console OAuthClient | Accepted redirect URIs (callback list) |
| Tunnel Deployment | Env block, image digest, replica count |
| Router | Deployed ConfigMap/Deployment identity and sha256 of the dispatch source |
| TLS secret | Name and type only — never the value |
| Operator conditions | `Available`, `Progressing`, `Degraded` at capture time |
| Timestamps | Capture start/finish, in UTC |
| Prior evidence | Reference to `restricted_rollback_snapshot_captured` in the October repair record |

## 2.6 Preconditions

All must be true before Step 1. Any false item postpones, it does not get
waived.

1. **Platform is powered on and healthy.** The 2026-11-16 scale-to-zero must be
   separately explained (or reversed) and the Deployments, CronJobs, routes,
   and tunnel all healthy. A powered-off cluster cannot host this window.
2. **Step 0 read-only check complete**, and the branch in §2.2 chosen and
   written down.
3. **Zero active lab records**, confirmed read-only, so no participant is
   mid-session during the change.
4. **Rollback capture committed and hashed** per §2.5.
5. **Deployed router matches the tested source** — the October record pins
   `deployed_router_sha256` `eb379b51f10a694351c4e56c077eeee176383e295aa5553e8a045dbfddc79f0c`.
   If the deployed hash differs, the counterfactual tests do not apply.
6. **Window approved in writing** by the Launchpad owner. The Flightpath/network
   owner's sign-off is waived per §2.11; every other item here still postpones
   rather than gets waived.
7. **A disposable one-seat test order is available** for the participant
   journey, and can be reclaimed through the normal workflow.

## 2.7 Window length and attendees

| Role | Name/owner | Required for |
|---|---|---|
| Launchpad owner | decision owner | Approve, accept criteria, sign the record |
| Flightpath/network owner | **waived 2026-11-24 (§2.11)** | Nothing — Launchpad owner covers operator patch, routes, tunnel and rollback |
| Platform SRE / on-call | — | Execute kubectl, rollback if triggered |
| Browser-verification operator | — | Native and participant Chrome checks |
| Security reviewer | — | Confirm no identity/RBAC drift |

**Estimated length: 90 minutes.** Rough split: 15 min Step 0 + capture, 20 min
cutover, 15 min operator reconcile and tunnel roll, 30 min browser journey and
reclaim, 10 min record and close-out. Rollback, if triggered, adds up to 30
minutes. Schedule outside business hours for the participant host.

## 2.8 Acceptance criteria

Taken from the October repair record's browser checks; all must pass:

- Native provider selection works; native kubeadmin login reaches the dashboard.
- Native logout returns to provider selection.
- Participant email/code login works.
- Showroom instructions and story render.
- Embedded Console shows the assigned namespace's pods.
- Embedded Console still works after refresh.
- Participant logout requires login again.
- The same email/code recovers the same seat.
- No new tab is required for participant Console.
- Authorization holds: assigned namespace can create Deployments; platform
  namespace cannot get pods; cluster nodes are not readable; after reclaim the
  namespace can no longer create Deployments.
- Disposable order reclaimed through the normal workflow; independent
  namespace, PVC, role-binding, Argo, and Showroom inventory reaches zero.

Browser success in one Chrome profile does not certify certificate trust on a
fresh device. That stays a separate, open item.

## 2.9 Risks and mitigations

| Risk | Mitigation |
|---|---|
| Operator reconcile re-adds or reverts routing | Watch `Progressing`/`Degraded`; re-read `spec.route` after reconcile; rollback R1 if it flaps |
| Both hosts return 503 during the tunnel roll | Roll tunnel last, one replica at a time; keep the old env captured for R3 |
| OAuth callback mismatch causes a login loop | Capture the callback list first; compare after reconcile before browser tests |
| Certificate trust warns on a new device | Separate item; do not bypass in the test browser, and do not claim it fixed |
| Participant embedded Console breaks but native works | Treat as a failed criterion; rollback, do not "note and proceed" |
| Platform unhealthy after power-on | Precondition 1; postpone rather than work around |
| Record omits the pre-cutover state | Capture is hashed and attached; no mutation before capture |
| The October repair was real, so this window is redundant | Step 0 decides; if already native, verify and close without mutating |
| Long-lived exception creep | The window is one-shot; no standing route override is left behind |
| **No network-owner present (§2.11)** | Step 0 read-only first, capture before mutation, and R1–R5 rollback run by the Launchpad owner with no shared-object step taken blind |

## 2.11 Accepted risk — second signature waived

On 2026-11-24 the Launchpad owner waived the Flightpath/network owner's
sign-off, on the stated basis that the Flightpath network will be fine. Recorded
here rather than deleted, because the window touches a shared router and the
Console operator's `spec.route` — objects the network owner normally owns.

What the waiver does **not** change:

- Step 0 stays read-only and stays mandatory. It is the only pre-mutation check
  that distinguishes "the October repair is live" from "the custom route is
  still in place", and it decides whether the window mutates anything at all.
- The rollback capture (§2.5) is still taken and hashed before any change.
- Preconditions 1–5 still postpone the window when false. Only the second
  signature is waived; a powered-off or unhealthy platform still blocks.
- If Step 0 finds the custom `spec.route` still in place, the Launchpad owner
  applies and owns the rollback, and the window record names that single owner
  instead of two.

What is genuinely weaker: there is no second reviewer between the person
changing shared routing and the change itself. That is the cost, and it is
accepted for one 90-minute window with a tested rollback.

## 2.10 Decision line — Brief 2

> **Decision 2:** Approve a single 90-minute native-route cutover window for
> the Console/`labs.smg-helix.ai` collision, preceded by a read-only Step 0
> check that either confirms the October repair is still in place (verify and
> close, no mutation) or confirms the custom `spec.route` remains (apply
> `deploy/console-embed/flightpath-native-route.patch.json` and roll the
> tunnel). No new DNS hostname. Record the window and rollback capture in
> `evidence/convergence/flightpath-console-cutover-<date>.yaml`. The window
> cannot open until the 2026-11-16 scale-to-zero is explained or reversed and
> the platform is healthy.
>
> Approved by: J Kershaw — Launchpad owner, 2026-11-24
> Flightpath/network owner: **sign-off waived by the Launchpad owner on
> 2026-11-24** ("flightpath network will be ok"). This is an accepted risk, not
> a satisfied precondition — see §2.11.
> Date: 2026-11-24 (window itself still blocked on preconditions 1–5)

---

## What this brief could not verify

| Claim | Why it is unverified | What would settle it |
|---|---|---|
| The two unrated matches are the same advisory counted twice | Retained scan JSON is a CI artifact, not in the repo | Read `backend-vulnerability-scan-95fec905...` and compare match IDs |
| `oc` is the only importer of `x/crypto/openpgp` | **Resolved: it is not.** `skopeo` in the showroom-terminal image links the same package under the same tag | Separate terminal disposition, or extend this one to two images |
| The current live Console `spec.route` value | Cluster is scaled to zero; no manifest in repo | Step 0 read-only `oc get` when powered on |
| Whether the October repair is still deployed | Oct 14 evidence and Oct 16/Nov 24 docs contradict | Same Step 0 read |
| Current `labs.smg-helix.ai` behaviour | Host returns 530 while scaled to zero | Re-check after power-on |
| Router deployed hash still matches `eb379b51...` | Not readable while scaled to zero | Read at Step 0 |
| Upstream `x/crypto` status after 2026-11-02 | Advisory could change after this brief's date | Re-read `vuln.go.dev` at signing |

## References

- `docs/staging-candidate-order-of-operations-20261016.md` — Phase 0 source.
- `docs/roadmap-convergence-20260929.md` — gate philosophy and closure rules.
- `docs/flightpath-orderable-capacity-and-roadmap-20261124.md` — Phase 0 still
  open; scale-to-zero note.
- `docs/flightpath-console-access-separation.md` — Console objects, repair,
  dedicated-hostname alternative, rollback requirements.
- `evidence/convergence/backend-security-95fec905-20261015.yaml` — 25 High,
  2 unrated, gate blocked.
- `evidence/convergence/image-remediation-20261020.yaml` — advisory meaning,
  `not_a_patch_version_fix`, `skopeo_unrated: [GO-2026-5932]`.
- `evidence/convergence/openpgp-compatibility-experiment-20261020.yaml` —
  ProtonMail fork rejected, 3/3 v3 signature failures.
- `evidence/convergence/backend-remaining-security-disposition-20261014.yaml`
  — record style and `oc` usage boundary.
- `evidence/convergence/flightpath-staging-readonly-preflight-20261014.yaml` —
  exact collision fields.
- `evidence/convergence/flightpath-native-console-repair-20261014.yaml` —
  claimed deployed state, rollback snapshot, browser checks.
- `backend/Containerfile` — `containers_image_openpgp`, `oc`/`helm` build, `oc`
  copied to `/usr/local/bin/oc`.
- `scripts/check_backend_staging_security.py` — `Unknown` blocks, including
  suppressed inventory; no allowlist.
- `deploy/console-embed/flightpath-native-route.patch.json` — cutover patch.
- `deploy/tunnel-oncluster/flightpath-deployment.yaml` — native Console host
  and callback env.
- `deploy/tunnel-oncluster/router.py` — path dispatch and URL rewrite.
- `deploy/launchpad/overlays/flightpath-candidate/candidate-clusters.yaml` —
  `public_console_url`.
- `backend/tests/test_flightpath_native_console_contract.py` — encoded cutover
  invariants.
- Upstream: `https://vuln.go.dev/ID/GO-2026-5932.json`.
