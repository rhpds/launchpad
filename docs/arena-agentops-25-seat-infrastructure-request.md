# Arena AgentOps 25-seat infrastructure request

## Request to Intel infrastructure

Provide **one additional Arena OpenShift worker host at minimum; two are
preferred** for the September 17 AgentOps workshop certification. Match the
existing CPU-worker networking, storage access, and 250-pod node capacity. The
hosts must join Arena as workers, not control-plane nodes.

Arena is a bare-metal cluster. Its `arena-86mfs-worker-0` MachineSet currently
has zero replicas and there are no available BareMetalHost objects: all three
registered hosts are unmanaged control-plane nodes. Increasing the MachineSet
replica count by itself therefore cannot add capacity. Intel must first attach
and register the worker hardware, or join equivalent worker nodes through its
approved bare-metal process.

## Why capacity is still required

The candidate AgentOps 0.1.4 contract reserves 12 steady pod slots, 2,500
millicores, 7,168 MiB memory, and 30 GiB storage per seat. It also reserves a
four-pod rollout/bootstrap burst for each of at most two seats provisioning at
once. Twenty-five seats therefore require:

| Resource | Required |
|---|---:|
| CPU | 62,500 millicores |
| Memory | 179,200 MiB |
| Pod slots | 308 (300 steady + 8 bounded transient) |
| Storage | at least 750 GiB |

Only `gnr2.fm2aihpcsed.com` is currently AgentOps-qualified. With a 250-pod
ceiling, the protected single-worker budget is 200 pods before subtracting
platform workloads. It cannot fit the 308-pod reservation. One equivalent
additional worker creates a 400-pod protected two-worker budget and is the
minimum theoretical topology, but the remaining margin must be re-measured
after DaemonSets and platform services land on that worker. A second additional
worker is preferred because it supplies practical failure and growth margin
instead of making the event depend on both workers remaining fully available.

No other registered cluster is a current baseline alternative. Oberon lacks
the complete AgentOps capability set. Brutus is reserved for emergencies and
also lacks the complete AgentOps operators and shared services. One workshop
will not be split across clusters.

## Worker acceptance criteria

Each new worker must:

- report `Ready=True` continuously for at least 15 minutes;
- expose 250 allocatable pod slots and enough aggregate CPU/memory for the
  reservation above;
- have no `NoSchedule`/`NoExecute` taint and no memory, disk, or PID pressure;
- reach Arena's internal image registry, API, ingress, DNS, NFS storage,
  shared LiteMaaS/model endpoints, shared embedding service, MLflow, logging,
  and OpenShift AI operators;
- bind and delete an ephemeral `launchpad-nfs-ephemeral` test PVC cleanly;
- pass image-pull, route, WebSocket terminal, and model-call probes; and
- remain unlabeled for AgentOps until the qualification run succeeds.

Launchpad will then apply
`launchpad.redhat.com/agentops-certified=true` to only the workers that pass,
rerun the 25-seat capacity preview, and require at least 25 supported seats
before it creates a workshop.

## Certification after delivery

The 25-seat release still requires 25/25 collective readiness, 25 simultaneous
participant journeys, namespace and cross-seat isolation, a 60-minute soak,
fault recovery, bulk reclaim, and zero remaining namespaces, Applications,
PVs, RoleBindings, sessions, or model-key material. Public access remains a
separate certification gate.
