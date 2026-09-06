# Multi-Agent Quickstart import

## Source

Launchpad imports the lab journey from
[`jkershawrh/multi-agent-quickstart`](https://github.com/jkershawrh/multi-agent-quickstart)
at immutable revision `8a8e0241265e69be81bf28060c4a96be38d5c244`.
The original repository remains the application and protocol source. Launchpad
owns the Antora/Showroom participant journey in
`content-multi-agent-quickstart` so runtime identity, namespace, model, and
cluster values are rendered for each seat.

This is a separate catalog item from the legacy `agent-swarm` visualization
and the larger `agentops-observability` workshop.

## Imported topology

The source Helm chart renders six application deployments: orchestrator,
three A2A agents, MCP server, and demonstration guardrails. The local source
also contains a Gradio UI, but the current OpenShift chart does not deploy or
route it. The source defaults to a mutable and currently inaccessible Quay
image and does not inject the Launchpad MaaS key into application pods.

For those reasons, the first import is deliberately a fail-closed draft. It
is source-complete and can be built by Antora, but is not orderable until the
Launchpad workload contract and live evidence are complete.

## Promotion gates

1. Publish the application image to a durable registry and pin its digest.
2. Add a participant UI Deployment, Service, and Route.
3. Inject the per-session MaaS endpoint and key from a runtime Secret without
   serializing secret values in Git or an Argo CD Application.
4. Label every resource with workshop, seat, session, tenant, and cluster IDs.
5. Add inference-aware readiness and a real workflow validation probe.
6. Prove participant route authorization and cross-seat denial.
7. Certify and reclaim one seat with zero residue.
8. Measure five seats and then twenty-five seats before raising the supported
   workshop limit.
