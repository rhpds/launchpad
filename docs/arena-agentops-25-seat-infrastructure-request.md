# Arena AgentOps 25-seat infrastructure request

## Request to Intel infrastructure

Provide **two additional Arena OpenShift worker hosts** for the September 17
AgentOps workshop certification. Match the existing CPU-worker networking,
storage access, and 250-pod node capacity. The hosts must join Arena as workers,
not control-plane nodes.

Arena is a bare-metal cluster. Its `arena-86mfs-worker-0` MachineSet currently
has zero replicas and there are no available BareMetalHost objects: all three
registered hosts are unmanaged control-plane nodes. Increasing the MachineSet
replica count by itself therefore cannot add capacity. Intel must first attach
and register the worker hardware, or join equivalent worker nodes through its
approved bare-metal process.

## Why two workers are required

The certified AgentOps contract reserves 17 pod slots, 2,500 millicores,
7,168 MiB memory, and 30 GiB storage per seat. Twenty-five seats require:

| Resource | Required |
|---|---:|
| CPU | 62,500 millicores |
| Memory | 179,200 MiB |
| Pod slots | 425 |
| Storage | at least 750 GiB |

Only `gnr2.fm2aihpcsed.com` is currently AgentOps-qualified. After the 20%
capacity reserve and its current 41 active pods, it offers 159 slots, or nine
seats. One additional 250-pod worker is insufficient: two qualified workers
provide only 400 protected slots before subtracting platform DaemonSets, less
than the 425-slot reservation. Two additional workers create three qualified
250-pod nodes and enough protected room for the workshop plus normal platform
pods.

No other registered cluster is a current alternative. Oberon has 37 protected
pod slots available and lacks the complete AgentOps capability set; even empty,
its 500-pod node retains only 400 slots after the required reserve. Brutus has
91 protected slots available, a 200-slot empty protected ceiling, and also
lacks the complete AgentOps operators and shared services. One workshop will
not be split across clusters.

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
