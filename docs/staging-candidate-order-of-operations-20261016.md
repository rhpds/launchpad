# Staging Candidate Order of Operations — 2026-10-16

Status: ACTIVE PLAN. This document sequences the remaining work to a qualified
Flightpath staging candidate after the 2026-10-16 CLI refresh and backend
security classification. It supersedes the sequencing discussion in the Oct 15
session for items whose state changed; release gates and evidence contracts
are unchanged.

Owner direction (2026-10-16): the platform is just out of pilot. Security
remains a concern with no waivers, but the immediate objective is clearing
fixable HIGH/CRITICAL findings pragmatically until lab-request traction
justifies deeper investment.

## Current gate state at plan time

| Gate | State | Evidence |
|---|---|---|
| Terminal image | Refreshed; 379 fixable matches (was 1,472); residue is entirely vendor-pending (go1.26.9/1.27.2 stdlib batch + dependency lag); helm clean, odo removed under owner authorization | `evidence/convergence/terminal-cli-refresh-20261016.yaml`, run 38918487384 |
| Backend image | 25 High + 2 unrated, all vendor-pending or advisory-review: distribution fix not consumable by oc (v3.1.0 removed the registry-client packages oc imports), 20 el9 RPM findings awaiting Red Hat errata, docker/docker 3H with no upstream fix, x/crypto GO-2026-5932 unrated deprecation advisory | `backend-security-95fec905-20261015.yaml`, Containerfile constraint note (506e739a) |
| Login/identity image | Qualified (0 High/Critical, signed, SBOM-attested, provenance-verified); NOT deployed — isolated upgrade + DB compatibility proof outstanding; historical promotion helper obsolete | `keycloak-security-candidate-20261015.yaml` |
| 501 Story API | Proven live for all three conditions; narrow-pane layout gate open | `v501-story-api-canary-20261015.yaml` |
| 401/501 catalog pins | Staged in the working tree, held for current-revision public browser proof | working tree, prior session |
| Console hostname | Canonical Console collides with `labs.smg-helix.ai`; cutover needs an approved window | `flightpath-staging-readonly-preflight-20261014.yaml` |

## Phase 0 — Owner decisions (blocking)

1. **x/crypto GO-2026-5932 disposition.** The advisory is an unrated
   "package unsafe by design" deprecation notice for the openpgp package
   with no fixed version in any release; it is not a traditional
   vulnerability. The zero-tolerance staging gate counts unrated matches as
   blocking, so a documented advisory-review decision is the only path for
   these two backend matches. Record the decision and its scope.
2. **Console cutover window.** Approve a coordinated window with rollback
   capture for the Console/hostname collision fix. Independent of all image
   work; can execute whenever approved.

Both items are now closed. Item 1 was signed on 2026-11-27
(`evidence/convergence/backend-openpgp-advisory-disposition-20261124.yaml`),
bound to the October scans with its limits recorded — it does not clear the
backend gate. Item 2 needed no window: the 2026-11-24 read-only check found no
operator `spec.route` override to cut over. Details in
`docs/phase-0-owner-decisions-20261124.md`.

Advice: make these decisions early — they are cheap, and Phase 2's timeline
does not clear them.

## Phase 1 — Now, in parallel (no live-service changes)

3. **Login fix isolated testing (critical path within our control).**
   Prove the Keycloak 26.8.1 candidate upgrade and database compatibility
   in an isolated namespace using a restored copy of the identity database;
   verify startup, schema migration, login, and existing-realm integrity.
   Replace the obsolete promotion helper with a path that targets the
   current launchpad-stage Deployment. No live identity service change
   until the isolated proof passes.
4. **501 layout fix.** Correct the narrow-pane primary-controls clipping in
   the virtualization-ai-501 presentation source; qualify through its
   release workflow and hold the new pins for the candidate freeze.
5. **Vendor watch.** Re-dispatch the terminal and backend release workflows
   when upstream tool releases or el9 errata land:
   - helm-style respins compiled with go1.26.9+ clear the stdlib batch;
   - dependency bumps (x/net, x/crypto, grpc, buildkit, fulcio, go-git,
     distribution) clear the module lag;
   - Red Hat el9 errata clears the RPM findings (verify via Red Hat
     security data, e.g. CVE-2026-53613, CVE-2026-19445).

   Contingency: if a single tool becomes the long pole, the skopeo-style
   immutable-source build exists as a pattern — but it is fork maintenance
   and is deliberately deferred until traction justifies it.

## Phase 2 — When the security gates pass (vendor-dependent)

6. Publish the terminal and backend images (`publish=true`); signing, SBOM
   and provenance verification are already wired and proven.
7. Deploy the login image: isolated-test-verified candidate first, then the
   live identity service swap with a database backup captured immediately
   before.
8. Deploy the refreshed backend and terminal images to Flightpath.

## Phase 3 — Convergence and freeze

9. Commit the staged catalog pins (sovereign-ai-101/301,
   virtualization-ai-401/501) and pin every image digest and source
   revision into one frozen candidate commit.
10. Run the exact-clean-commit regression; working-tree green (2,914 passed
    on 2026-10-16) does not substitute.
11. Terminal browser proof on the deployed image: reconnect preserves the
    shell; logout, expiry and reclaim terminate access.
12. Current-revision public browser proof for virtualization 401/501 and
    the sovereign 201 source-bound proof; then promote the catalog pins.
    These stay last by design — they validate the frozen candidate.

## Phase 4 — Acceptance and close

13. Execute the Console hostname cutover in the approved window.
14. Full Flightpath acceptance sweep: requester → order → admin visibility
    → participant login → Showroom, workspace, terminal, Console →
    resume/logout → reclaim, with zero-residue cleanup verified.
15. Close the staging evidence package: zero cleanup residue, current
    evidence references, no unresolved mandatory failures, and explicit
    staging acceptance recorded.

## Dependency notes

- Phase 2 blocks on vendors; Phase 3 items that touch the new images block
  on step 8. Everything in Phase 1 can proceed now.
- Step 3 is the longest pole we control — start it immediately so the login
  gate is closed by the time images clear.
- Catalog public proofs (step 12) deliberately run against the frozen
  candidate; running them earlier forces a re-run.
- No security exceptions, suppressions, or scanner ignores at any step.
