# Network Operations unified Showroom: Flightpath 25-seat certification

Certification date: 2026-09-24  
Maximum certified seats: 25 in one workshop  
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
- Launchpad backend source revision: `ee92d4bdcb283ceebad02c2e6517ba339b2174c5`
- Signed and attested backend image:
  `ghcr.io/rhpds/launchpad-backend@sha256:c12c36c485b310dd55f7dd0e16cf333ada0e3b393269649d62fe351eccc7b14c`
- Backend release workflow:
  <https://github.com/rhpds/launchpad/actions/runs/36079597871>
- Workshop: `ea697ce5-d16b-40de-bc04-e9bc676abf41`

## Capacity and provisioning evidence

- The capacity gate assigned the entire 25-seat workshop to Flightpath and
  retained 20% headroom. The estimate was 2.5 CPU cores, 6.25 GiB memory, and
  50 pod slots.
- The admin-only certification override matched the next declared promotion
  target of 25 while the public catalog limit remained five.
- Serialized provisioning reached 25 ready seats in approximately 16 minutes.
  There were no failed or partial seats.
- All 25 sessions targeted Flightpath, selected `granite-3.2-8b-tools`, used
  distinct LiteLLM virtual keys, and produced 125 passing platform validation
  checks with zero failures.
- The workshop ran 75 pods and 150 ready containers with zero not-ready
  containers. Workloads were scheduled across `fp1` and `fp2`; node spreading
  was not required by this catalog item.
- All 50 workload containers used the exact signed workload digest.
- All 50 GitOps Applications were `Synced` and `Healthy`. Every Showroom used
  the exact content revision and exposed Story, Terminal, Network Operations
  Workspace, and namespace-scoped OpenShift Console.

## Concurrent participant evidence

- Twenty-five simultaneous checks returned HTTP 200 for every Showroom,
  terminal, Story page, and hashed Story asset.
- Twenty-five simultaneous hardware investigations returned
  `hardware_timing` with evidence `hardware-1`.
- Twenty-five simultaneous platform investigations returned
  `platform_timing` with evidence `openshift_platform-1`.
- Hardware investigation latency was 10.2 seconds minimum, 11.0 seconds median,
  and 14.1 seconds maximum.
- Platform investigation latency was 10.3 seconds minimum, 11.0 seconds median,
  and 14.2 seconds maximum.
- Every terminal ran as `lab-user`, opened in its assigned namespace, could
  read that namespace's pods, and could not read cluster nodes.
- Every seat retained the diagnostics ingress NetworkPolicy, and no diagnostics
  Service had a public Route.

## Bulk reclaim evidence

- One workshop reclaim transitioned all 25 seats to `reclaimed` in
  approximately 96 seconds with zero failed seats.
- LiteLLM returned confirmed HTTP-success revocation receipts for all 25 unique
  virtual keys.
- All 50 GitOps Applications and every workshop-labelled resource disappeared.
- All 25 namespaces reached absence.

## Boundary

This receipt certifies one internal Flightpath workshop with up to 25 seats for
the exact immutable revisions above. It does not certify public access,
multiple concurrent workshops, cross-cluster placement, production SLOs, or
real-network remediation. Public-code access and concurrent-workshop capacity
remain separate gates.
