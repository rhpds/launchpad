# Remote execution-cluster registration

Arena is the current local control and execution cluster. Oberon and Brutus are
registered in the Arena cluster-target ConfigMap as disabled remote targets.
They must remain disabled until the complete procedure below and the catalog's
1 -> 5 -> 25 live certification are green.

As of 2026-09-05, Brutus has passed the one-seat infrastructure, Showroom,
terminal, Build-an-Agent tool-calling, namespace-isolation, and zero-residue
reclaim gate. It remains disabled for normal placement until durable image
promotion replaces the certification-only local mirror and the five- and
twenty-five-seat gates pass. Oberon remains at the infrastructure probe gate.

Apply `arena-rbac.yaml` to the remote cluster, create a bound service-account
token, and build a kubeconfig for that identity. Despite the historical
filename, this is the shared Launchpad provisioner RBAC contract. Store the
kubeconfig on Arena without committing it:

```sh
KUBECONFIG=/explicit/arena-admin.kubeconfig oc \
  -n partner-ai-launchpad create secret generic launchpad-brutus-kubeconfig \
  --from-file=kubeconfig=/secure/path/brutus-launchpad.kubeconfig
```

Use `launchpad-oberon-kubeconfig` for Oberon. The Secret names and namespaces
must exactly match `credential_secret` in `config/clusters.yaml`.

Apply `arena-argocd-rbac.yaml` to the remote cluster with an explicit
kubeconfig, then register that separate Argo identity in Arena's existing Argo
CD using its supported cluster-secret workflow. The Argo destination servers
must exactly match the registry:

- Brutus: `https://api.brutus.fm2aihpcsed.com:6443`
- Oberon: `https://api.oberon.fm2aihpcsed.com:6443`

Never copy kubeadmin credentials into Launchpad or Git.

Build the control-plane trust bundle from explicit, authenticated kubeconfigs
before enabling an HTTPS model endpoint on a remote target:

```sh
scripts/install-cluster-ca-bundle.sh \
  /secure/arena-admin.kubeconfig \
  partner-ai-launchpad \
  backend \
  /secure/arena-admin.kubeconfig \
  /secure/brutus-admin.kubeconfig \
  /secure/oberon-admin.kubeconfig
```

The script combines the backend image's system roots with every execution
cluster ingress chain, mounts the result, and enables verification for both
`httpx` and `requests`. Launchpad copies that bundle into model-consuming seat
namespaces. Re-run it whenever an ingress certificate rotates; never disable
TLS verification to make a remote model probe pass.

The Argo identity has cluster-wide read access because its cache discovers
cluster resource kinds, while mutation remains limited to the resources used
by Showroom. Do not reuse the Argo credential for Launchpad provisioning.

Before enabling a remote target, prove all of the following from the Arena
control plane:

1. Launchpad and Argo credentials resolve and have only the documented access.
2. Namespace, Route, PVC, workload, Showroom, validation, and reclaim target
   only the persisted remote `cluster_ref`.
3. Durable external images pull without relying on another cluster's internal
   image registry. Pre-seed and verify every immutable digest before opening an
   order; the Brutus one-seat run measured a 10m42s cold terminal-image mirror
   and one resumable HTTP 408 while moving the agent image.
4. Every required model endpoint is reachable from the remote workload network
   and is explicitly registered; do not substitute Brutus's Granite 3.1 GPU
   endpoint for a Xeon CPU or Granite tools contract without a content and
   functional re-certification.
5. Private ingress, WebSockets, Console/OIDC, storage deletion, and zero-residue
   cleanup pass one seat before five and twenty-five seats are attempted.
6. Public placement remains disabled until stable DNS/TLS and the per-cluster
   public-access matrix are independently GREEN-live.

All workstation operations must use `KUBECONFIG=/explicit/path`; never switch
or rely on the default kubeconfig context.
