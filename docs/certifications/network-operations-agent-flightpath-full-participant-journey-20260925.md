# Network Operations Agent: Flightpath full participant journey

## Certification identity

- Date: 2026-09-25
- Cluster: `flightpath`
- Catalog item: `network-operations-agent`
- Catalog version: `0.2.0-flightpath.10`
- Source revision: `287bffcca9c90336ed199ab2156d4471377b2c3e`
- Runtime image: `ghcr.io/jkershawrh/network-operations-agent@sha256:74afaf7d26791327fe4d1d7e5f302c7532b644f8d902daf1e914f9c2c4e5faf1`
- Source CI: GitHub Actions run `36164697371` passed
- Workshop: `8d664daf-a892-4f0c-a741-de6922158111`
- Session: `7fe9da89-b86a-428e-a8eb-56ba2bdd2308`
- Seat: `ae9b2955-b5b4-4625-bb4b-cb01d7da51e1`
- Namespace: `launchpad-network-ops-certif-network-ops-ae9b29`
- Public participant URL: `https://labs.smg-helix.ai/labs/network-operations-agent-8d664daf`

The one-time instructor code is intentionally excluded from repository evidence.

## Provisioning and route evidence

- Workshop reached `ready` on the persisted `flightpath` target.
- Application, diagnostics, and four-container Showroom pods were ready with zero restarts at certification time.
- The application Route used the portable short name `netops`.
- The Showroom Route and the `/api`, `/health`, `/story`, and `/workspace` same-origin proxy Routes all passed Launchpad validation.
- The application `/ready` endpoint returned `status=ready`.
- Full-lab mode was enabled: `/api/lab/investigate` returned bounded input validation rather than `404`.

## Participant access and isolation evidence

The public order was claimed through the normal code flow in a clean participant browser session. The participant terminal proved:

- its current project was the assigned namespace;
- pod read access and deployment create access were allowed in that namespace;
- cluster-scoped node access was denied; and
- pod access to the Launchpad control namespace was denied.

Both Network Operations workload deployments had service-account token automount disabled. Both workload Services were `ClusterIP`, the diagnostics service had no public Route, and its NetworkPolicy was present.

## Complete hands-on journey

The seven-module journey was executed from the actual Showroom terminal container.

- Baseline hardware incident: three current observations, cause `hardware_timing`, human approval required, no action executed.
- Baseline platform incident: three current observations, cause `platform_timing`, human approval required, no action executed.
- Approved MCP boundary: four exact read-only diagnostic tools discovered.
- Learner-authored incident: cause `upstream_timing`, support `upstream_timing-1`, no action executed.
- Unsafe extension: an added `restart-grandmaster` command was rejected with HTTP 400 and was not reflected in the response.
- Reliability qualification: five of five scenarios passed, including fail-closed timeout, conflict, and malformed-tool behavior.
- Provenance: all four learner observations carried timestamps and provenance.
- Evidence package: scenario, investigation, qualification, checksums, and NOC decision brief were generated in participant storage.

Terminal completion marker:

`FULL_LAB_PASS namespace=launchpad-network-ops-certif-network-ops-ae9b29 hardware=hardware_timing platform=platform_timing learner=upstream_timing qualification=pass scenarios=5 action_executed=false evidence_files=5`

## Browser journey

- The participant landing page recovered the assigned seat and opened the lab on the same origin.
- The guide rendered the new 90-minute, seven-module content.
- The Story tab rendered the current Triforce journey with offline Red Hat and Intel logos.
- The Network Operations Workspace stayed embedded and returned the hardware-timing recommendation, current evidence, historical context, uncertainty, and human-review boundary.
- The OpenShift Console stayed inside the Showroom tab, completed SSO without a second credential prompt, opened the exact assigned namespace, and displayed the three expected pods.
- Selecting the OpenShift Console tab did not navigate the top-level browser or open a new tab.

## Supporting automated tests

- Network Operations source suite: 67 passed.
- Launchpad focused catalog, workshop, public-access, gateway, tunnel, and multicluster suites: 220 passed before the final catalog correction.
- Launchpad focused catalog/workshop regression suite after enabling full-lab mode: 110 passed.
- Kubernetes decimal memory quantity regression confirms both decimal (`500M`, `1G`) and binary (`512Mi`, `2Gi`) capacity inputs.

## Defects found and corrected during certification

1. Flightpath capacity inspection rejected valid decimal-SI memory requests such as `500M`. The parser now supports Kubernetes decimal and binary quantities.
2. A long workload Route name combined with the generated namespace exceeded OpenShift's 63-character host-label limit. The catalog now uses the portable Route name `netops`, and the guide discovers it by workload labels.
3. The full learner APIs were left at the chart's safe default (`lab.enabled=false`). Catalog version `0.2.0-flightpath.10` explicitly enables them.

This evidence certifies the one-seat Flightpath participant journey. It does not by itself promote a higher public seat count or certify production scale.
