# Network Operations unified Showroom: Flightpath one-seat certification

Certification date: 2026-09-24  
Maximum certified seats: 1  
Execution cluster: Flightpath  
Exposure policy: `internal`  
Inference path: Flightpath LiteLLM gateway to Flightpath CPU vLLM  
Model: `granite-3.2-8b-tools`

## Immutable release

- Network Operations source revision: `b672eaf74467ef2e853befe3bdb3b34a3264a24c`
- Signed workload image:
  `ghcr.io/jkershawrh/network-operations-agent@sha256:b240a34670db3009ec827ebe35dcb62bc5ae3ddd423b975fee08b17e114a040d`
- Workload release workflow:
  <https://github.com/jkershawrh/network-operations-agent/actions/runs/36076213007>
- Launchpad source revision containing the path-aware Showroom contract:
  `6fe0667a62cb26e2d4f0cc8ca5d7798e6aa729df`
- Flightpath backend candidate:
  `quay.io/rh-ee-jkershaw/launchpad-backend@sha256:a94d8cf3002906c78d6db111c6645a19210ac632ce1dde43ed3a5a37b4dc7453`
- Launchpad backend build workflow:
  <https://github.com/rhpds/launchpad/actions/runs/36076724163>
- Workshop: `062e8d02-fbe1-4979-bc2b-f70376a0328c`
- Seat: `a1a77b02-94d8-4028-884d-af82a05bea87`
- Request: `0c9dd183-137a-4ffe-a541-c04b1b67e260`
- Session: `a071fefc-9d87-4bd8-8d97-c679fb619f27`

The backend workflow passed its exact-revision build, vulnerability inventory,
fixable-high/critical gate, and SBOM generation. Publication could not use the
repository's CI identity because the Quay credentials are not configured in
GitHub Actions. The exact image was therefore published with the existing local
Quay identity for this internal one-seat certification. It is not approved for
promotion beyond this gate until CI publication, signing, and attestation are
restored.

## Red/green evidence

- Capacity admission selected `flightpath` for the complete one-seat workshop
  before creating resources.
- The workshop and seat reached `ready`; the application, diagnostics, and
  four-container Showroom pods were all ready.
- The workload pods used the exact signed GHCR digest. Both GitOps Applications
  were `Synced` and `Healthy`.
- The Showroom and workspace Routes returned HTTP 200.
- The Story page and its hashed JavaScript asset returned HTTP 200 and rendered
  the Red Hat and Intel branded presentation at `/story/`.
- The generated Showroom configuration exposed four coherent paths: Story,
  Terminal, Network Operations Workspace, and namespace-scoped OpenShift
  Console.
- The source and rendered Showroom both contained the four-depth journey:
  presentation story, live demonstration, guided demo, and hands-on lab.
- Live hardware and platform investigations returned distinct correct causes,
  current evidence IDs, three observations, mandatory human approval, and no
  executed remediation.
- The terminal started as `lab-user` in the assigned namespace. It could read
  namespace pods and could not read cluster nodes.
- The diagnostics service had no public Route and retained its ingress
  NetworkPolicy.
- Reclaim completed with no failed seats. LiteLLM key revocation was confirmed,
  both GitOps Applications and all session-labelled resources disappeared, and
  the namespace reached absence.

## Boundary

This receipt certifies one internal Flightpath seat for the exact immutable
revisions above. It does not certify public access, five or 25 seats,
concurrent provisioning, production SLOs, or the unsigned Flightpath backend
candidate for broader promotion. Those remain later gates.
