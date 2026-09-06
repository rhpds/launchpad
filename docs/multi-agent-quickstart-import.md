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

## Launchpad seat topology

The upstream source remains immutable. Launchpad builds that exact revision,
adds model bearer-token support and a compatible pinned UI dependency, and
publishes the certification image by digest. The Launchpad-owned
`deploy/workloads/multi-agent-seat` chart runs the orchestrator, three A2A
agents, MCP server, demonstration guardrails, and Gradio participant UI as
seven containers in one workload pod. Services preserve the upstream protocol
boundaries, and separate Routes expose only the participant UI and
orchestrator. A second pod provides Showroom and its namespace-scoped terminal.

Every workload resource carries workshop, seat, session, tenant, and cluster
ownership labels. Launchpad creates a per-seat `multi-agent-runtime` Secret for
the selected model endpoint, model identifier, MaaS key, and generated service
token. The Secret is applied directly to Arena and only its name is passed to
Argo CD.

The catalog remains a fail-closed draft with a one-seat ceiling. The first live
run reached the functional one-seat gate after a regression retry and then
reclaimed with zero residue. That run is recorded in
`evidence/multi-agent-one-seat-live-2026-09-05.json`; it does not certify a
clean first pass, public access, or workshop scale.

## Repeatable onboarding and certification

Catalog onboarding is repository-driven rather than a collection of manual
cluster edits:

1. Change `catalog-onboarding/multi-agent-quickstart.yaml`.
2. Render `catalog/multi-agent-quickstart/catalog-item.yaml` with
   `scripts/catalog_onboarding.py render`.
3. Validate the intake, Showroom, and workload sources with
   `scripts/catalog_onboarding.py validate --fetch --build-showroom`.
4. Run the local chart and onboarding contracts.
5. Build the pinned image from the declared upstream revision.
6. Provision one draft certification seat through the admin workshop API.
7. Run `scripts/certify-multi-agent-seat.sh <namespace>` with an explicit Arena
   `KUBECONFIG`.
8. Reclaim through Launchpad and record hashed zero-residue evidence.

## Promotion gates

1. Run a fresh order from the final corrected catalog and require a clean
   first-pass ready result.
2. Mirror the digest-pinned image from Arena's certification registry to a
   durable external registry or durable control-plane mirror.
3. Certify public-code participant authentication, route authorization, and
   cross-seat denial for this catalog item.
4. Measure five seats, including concurrent model traffic and complete
   zero-residue reclaim.
5. Measure twenty-five seats before raising the supported workshop limit.
6. Require three consecutive twenty-five-seat passes before general
   availability.
