# AgentOps seat chart

This Launchpad-owned chart is the namespace-scoped participant portion of the
RHDP AgentOps experience. It deliberately does not install operators,
cluster-scoped RBAC, ConsoleLinks, namespaces, shared MLflow, or logging.

Launchpad must create `runtime.existingSecret` directly in the seat namespace
before Argo CD applies this chart. At minimum the Secret supplies:

- `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`;
- `DATABASE_URL` and `COMPLIANCE_DATABASE_URL`;
- `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_ENDPOINT`, `S3_BUCKET`, and `S3_REGION`;
- `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_MODEL_FAST`, and
  `LLM_MODEL_CAPABLE`;
- `AUTH_DISABLED`, `COMPANY_NAME`, `AGENT_NAME`, `DEBUG`, and `ALLOWED_HOSTS`;
  and
- the MLflow configuration consumed by the Mortgage AI API.

The chart renders no Kubernetes Secret. Generated credentials and model keys
therefore never enter an Argo CD Application or Git history. The runtime
Secret and every rendered resource carry session, workshop, seat, tenant, and
cluster ownership labels so cleanup can remain deterministic.

Disposable seat PVCs use Arena's `launchpad-nfs-ephemeral` StorageClass. Its
`Delete` reclaim policy and disabled NFS archive behavior are part of the
cleanup contract: reclaim must delete both the PV object and its NFS subdirectory.
Do not use Arena's general `nfs-storage` class for participant seat data because
its `Retain` policy leaves Released PVs and their data behind.

The upstream source and revision from which this chart was derived are pinned
in `Chart.yaml`. The direct chart, shared embeddings, MLflow trace, DSPA, and
automatic reclaim have live component evidence. Activation still requires
image digest pinning, trusted and entitlement-protected participant routes,
OpenShift Logging, and a complete Launchpad-created one-seat journey.
