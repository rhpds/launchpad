# Network Operations unified Showroom: Flightpath five-seat certification

Certification date: 2026-09-24  
Maximum certified seats: 5  
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
- Launchpad source revision: `ee92d4bdcb283ceebad02c2e6517ba339b2174c5`
- Signed and attested backend image:
  `ghcr.io/rhpds/launchpad-backend@sha256:c12c36c485b310dd55f7dd0e16cf333ada0e3b393269649d62fe351eccc7b14c`
- Backend release workflow:
  <https://github.com/rhpds/launchpad/actions/runs/36079597871>
- Workshop: `a8740421-c382-4cbb-9148-c2854ac46d7e`
- Sessions:
  - `7ce8fde9-f925-41ab-9854-4585731035b7`
  - `1b27691b-6018-46d8-b256-136ce89b3910`
  - `681d1ee3-4c40-4a0b-934d-e0548613f673`
  - `5dc20aaa-df59-40c5-b70e-0a8bdfdb30ef`
  - `edf5b744-3c65-400f-8cf5-5b3194438c1f`

## Supply-chain evidence

- The backend release bound checkout and build to the exact 40-character source
  revision.
- Vulnerability inventory completed and the fixable high/critical blocking gate
  passed.
- The workflow retained vulnerability reports and an SPDX JSON SBOM.
- GitHub OIDC produced the keyless signature and build-provenance attestation.
- Flightpath pulled the exact GHCR digest in a disposable pod, ran it
  successfully, and removed the probe before deployment.
- Backend, lifecycle worker, public gateway template, and lifecycle scheduler
  were pinned to the same digest. Backend and worker rolled out successfully.

## Provisioning and participant evidence

- Capacity admission selected Flightpath for the entire workshop and retained
  20% headroom. The admin-only override matched the next promotion target of
  five while the public catalog limit remained one.
- Serialized provisioning created five sessions with no failed or partial
  seats. Each session had five passing platform validation checks and no
  failures.
- All 15 participant pods were ready. All ten GitOps Applications were `Synced`
  and `Healthy`.
- Every application and diagnostics container used the exact signed workload
  digest, and every Showroom checkout used the exact source revision.
- Every generated Showroom exposed Story, Terminal, Network Operations
  Workspace, and namespace-scoped OpenShift Console.
- Showroom, terminal, story, and hashed story assets returned HTTP 200 for all
  five seats.
- Five simultaneous hardware investigations returned `hardware_timing` with
  evidence `hardware-1`. Five simultaneous platform investigations returned
  `platform_timing` with evidence `openshift_platform-1`.
- Concurrent investigation latency ranged from approximately 9.4 to 12.0
  seconds.
- Every terminal ran as `lab-user`, opened in its assigned namespace, could
  read that namespace's pods, and could not read cluster nodes.
- All five sessions received distinct LiteLLM virtual keys.

## Reclaim evidence

- One bulk reclaim transitioned all five seats to `reclaimed` with no failed
  reclaims.
- LiteLLM returned confirmed HTTP-success revocation receipts for all five
  virtual keys.
- All ten GitOps Applications and every workshop-labelled workload resource
  disappeared.
- All five namespaces reached absence.

## Boundary

This receipt certifies up to five internal Flightpath seats for the exact
immutable revisions above. It does not certify public access, 25 seats,
multiple concurrent workshops, production SLOs, or real-network remediation.
The catalog must remain capped at five until the 25-seat gate passes.
