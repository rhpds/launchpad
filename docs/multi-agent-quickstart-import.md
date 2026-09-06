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

## One lab, three tracks

The catalog item preserves the three learning tracks from the upstream
quickstart inside one Showroom and one provisioned participant environment:

1. **Track 1 — Run locally:** source-guided study of the application topology,
   A2A discovery, routing, MCP, and guardrails. In Launchpad, participants use
   the pre-provisioned application rather than starting nested Docker Compose.
2. **Track 2 — Deploy to OpenShift:** live operation of the application in the
   participant's namespace. This is the currently certified runtime path.
3. **Track 3 — Advanced blueprint alignment:** architecture and manifest
   exploration for Kagenti, OpenTelemetry, workload identity, policy, and
   supported guardrails. Optional components are not presented as deployed
   unless the target cluster has separately certified them.

These are learning paths, not separate catalog records, seats, or model
deployments. The Showroom welcome page is the track chooser, and all tracks use
the same terminal, Workspace, namespace, and TTL.

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

The catalog remains a fail-closed draft with a one-seat ceiling. The corrected
runtime first reached the functional gate after a regression retry; a second,
fresh order then reached `ready` on its first attempt without a live patch and
reclaimed with zero labeled residue. The runs are recorded in
`evidence/multi-agent-one-seat-live-2026-09-05.json` and
`evidence/multi-agent-one-seat-clean-live-2026-09-05.json`. A subsequent fresh
order proved the three-track chooser and every track page in one environment;
see `evidence/multi-agent-three-track-showroom-live-2026-09-06.json`. The
reusable framework then proved one five-seat workshop with concurrent checks on
every seat, complete isolation, and zero-residue reclaim; see
`evidence/runs/multi-agent-quickstart-5-seat-multi-agent-5seat-20260906-01.json`.
Together they certify the shared runtime and Track 2 internal five-seat gate,
but not every optional Track 3 integration, public access, or 25-seat scale.

The first 25-seat attempt, `multi-agent-25seat-20260906-01`, is intentionally
retained as RED evidence and does not count toward promotion. Arena worker
`rhgnr1` stopped reporting after 24 seats were ready; the Launchpad backend,
single-replica internal registry, and both Kueue controller replicas were all
concentrated on that worker. The API returned 503, the registry temporarily had
no endpoint, and stale Kueue discovery initially blocked namespace deletion.
Persisted workshop recovery completed reclaim after the node returned, the
Kueue visibility APIs were restored, and an independent audit reached zero
residue. The generic runner now retries bounded connection and 502/503/504
failures so a transient control-plane interruption does not discard its live
observation window. See the run and fault records under `evidence/runs/`.

The second attempt, `multi-agent-25seat-20260906-02`, brought all 25 seats to
Ready and passed every participant, Showroom, agent workflow, isolation,
secret-safety, and model-key revocation check. It remains RED and uncounted
because the first residue sample ran immediately after workshop completion,
while 20 namespaces were still terminating; an independent follow-up reached
zero without intervention. The runner now polls all declared cleanup resource
types to zero within the same cleanup SLO before scoring the cleanup gate.

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
6. Validate the reusable proof contract:
   `scripts/catalog_certification.py validate
   certification/catalog/multi-agent-quickstart.yaml`.
7. Inspect the deterministic 1-, 5-, or 25-seat plan with
   `scripts/catalog_certification.py plan`.
8. Execute `scripts/catalog_certification.py run` with an explicit Arena
   `KUBECONFIG` and the API key supplied only through the environment.
9. The generic runner calls `scripts/certify-multi-agent-seat.sh` for every
   ready namespace, then reclaims the whole workshop and records hashed
   zero-residue evidence.

## Promotion gates

1. Mirror the digest-pinned image from Arena's certification registry to a
   durable external registry or durable control-plane mirror.
2. Certify public-code participant authentication, route authorization, and
   cross-seat denial for this catalog item.
3. Measure twenty-five seats before raising the supported workshop limit.
4. Require three consecutive twenty-five-seat passes before general
   availability.
