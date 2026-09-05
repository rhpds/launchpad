# Catalog onboarding pipeline

Launchpad catalog onboarding is Git-first and evidence-gated. A content
integrator declares a lab once in `catalog-onboarding/<catalog-id>.yaml`; the
pipeline renders and validates its draft catalog record, checks immutable
Showroom and workload sources, builds the Antora site, and emits a JSON receipt.

This removes the repeated hand-editing of catalog metadata, source revisions,
resource estimates, tab declarations, and certification gates. It does not
automatically make an untested lab orderable. Runtime integration and live
certification remain explicit promotion gates.

## Source-of-truth contract

Each intake declares:

- catalog ID, title, description, category, and version;
- immutable Showroom repository SHA, playbook, and Antora start path;
- immutable workload repository SHA, packaging type, and deployment path;
- required cluster capabilities and models;
- conservative per-seat CPU, memory, pod, and storage estimates;
- the complete participant tab contract;
- the current certification stage, supported seat ceiling, promotion sequence,
  and every activation blocker.

The corresponding `catalog/<catalog-id>/catalog-item.yaml` is generated from
that contract. Intake-managed entries are always rendered as `draft`. Changing
them to `active` is a separate, reviewed promotion after the blockers are
cleared and the evidence has been accepted.

## Local workflow

Render a catalog record:

```bash
.venv/bin/python scripts/catalog_onboarding.py render \
  catalog-onboarding/<catalog-id>.yaml \
  --output catalog/<catalog-id>/catalog-item.yaml
```

Validate local source checkouts:

```bash
.venv/bin/python scripts/catalog_onboarding.py validate \
  catalog-onboarding/<catalog-id>.yaml \
  --catalog catalog/<catalog-id>/catalog-item.yaml \
  --showroom-dir /path/to/showroom \
  --workload-dir /path/to/workload \
  --build-showroom \
  --antora-bin node_modules/.bin/antora
```

Validate the exact remote commits as CI does:

```bash
.venv/bin/python scripts/catalog_onboarding.py validate \
  catalog-onboarding/<catalog-id>.yaml \
  --catalog catalog/<catalog-id>/catalog-item.yaml \
  --fetch \
  --build-showroom \
  --antora-bin node_modules/.bin/antora \
  --report test-receipts/catalog-onboarding-<catalog-id>.json
```

The command exits nonzero for a malformed intake, mutable Git reference,
missing content/page/image, missing workload package, failed Antora build, or
catalog drift. An intact draft with declared activation blockers passes source
validation and reports `activation_status: blocked`; this is intentional.

## Pull-request automation

The `Catalog Onboarding Contracts` CI job discovers every YAML file under
`catalog-onboarding/`. For each intake it:

1. fetches the pinned Showroom and workload revisions;
2. validates Antora playbook, component, navigation, pages, and local images;
3. validates the declared Helm, Kustomize, or manifest package;
4. compares the generated record with the committed catalog YAML;
5. builds the complete Showroom through Antora; and
6. uploads a machine-readable validation receipt.

Adding another intake does not require a workflow change.

## Promotion path

The automated source gate is only the first layer:

1. **Intake:** source and package checks pass; catalog remains `draft`.
2. **Runtime integration:** per-seat configuration, routes, secrets, labels,
   readiness, validation, and deterministic cleanup are implemented.
3. **One seat:** a participant completes the real journey and reclaim leaves no
   residue.
4. **Five seats:** concurrency, isolation, model behavior, and shared services
   are measured.
5. **Twenty-five seats:** the intended workshop envelope is certified with
   participant-facing, performance, failure-recovery, and cleanup evidence.
6. **Activation:** reviewers remove resolved blockers, update measured resource
   values and certification stage, and explicitly promote the catalog item.

Large labs may stop at a lower certified seat ceiling. The catalog must publish
the measured safe limit rather than copying the platform-wide maximum.

## AgentOps intake status

The detailed RHDP topology and Launchpad adaptation decisions are recorded in
[agentops-rhdp-gap-analysis.md](agentops-rhdp-gap-analysis.md).

`agentops-observability` is registered as a draft candidate from:

- Launchpad Showroom: `rhpds/launchpad`,
  `content-agentops-observability`, at
  `59563b0a77252e8b91077c30c23ab524a8402bce`;
- upstream Showroom provenance: `rhpds/agentops-intel-showroom` at
  `f1881c61de55ebf5640c27e76469f4efe458edaf`;
- Launchpad seat chart: `rhpds/launchpad`, `deploy/workloads/agentops-seat`, at
  `e177a2fa92533d23b7e7846c93efe08a9a63493b`;
- referenced RHDP automation: `rhpds/agentops-in-prod-automation` at
  `6ea100531ac869fa66abe69ae223d6b56dbce9a2`;
- transitive Mortgage AI application: `rh-ai-quickstart/multi-agent-loan-origination`
  at `1e50e51c334c1b6ed854d81a3f28fd324792f481`.

The RHDP deployment path was also traced through AgnosticV
`agd_v2/agentops-intel` at
`48fc6eebedb295bddf1b915a230e5e90f89db0af`. That configuration does not
deploy the application chart directly. It runs the bootstrap chart from
`rhpds/agentops-in-prod-automation` at
`6ea100531ac869fa66abe69ae223d6b56dbce9a2`. That repository is retained as
immutable provenance, but it is not Launchpad's deployable workload source.
The deployable source is the Launchpad-owned namespace-scoped seat chart at
`e177a2fa92533d23b7e7846c93efe08a9a63493b`. The application repository remains
recorded as transitive source provenance.

Its source and Antora build pass. The Launchpad-owned component replaces the
fixed RHDP username/password and `wksp-user1` namespace with participant SSO
and generated seat values, pins the PatternFly 6 UI and application sources,
and describes the Arena `granite-3.2-8b-tools` target. The upstream screenshots
and instructional flow remain attributed at their immutable revision.

It is not orderable because the complete live experience still requires the
pre-provisioned mortgage application, shared MLflow, per-seat Grafana,
OpenShift Logging, user workload monitoring, OpenShift AI workbenches and
pipelines, and eight authorized environment tabs.

The RHDP automation is a workshop-scoped app-of-apps. It installs cluster-global
Applications named `mlflow`, `logging`, `cluster-monitoring`, `image-puller`,
and `openshift-ai`, then uses ApplicationSets for each `wksp-userN` namespace.
Those global names make the unmodified bootstrap unsafe for concurrent
Launchpad orders. Launchpad installs compatible shared Arena services once and
generates only uniquely owned, namespace-scoped seat resources per order.
The current AgnosticV catalog declares `num_users: 1` and
`workshop_user_mode: single`; 5- and 25-seat use is a new Launchpad
certification target, not a capability inherited from the RHDP item.
The upstream bootstrap also places the LiteMaaS virtual key in Helm values,
which would expose it in the Argo CD Application. The Launchpad adapter now
creates an idempotent runtime Secret directly through the Arena API and passes
only the Secret name to Argo CD. Generated database and object-storage
passwords, the LiteMaaS endpoint/key, requested model, and composed connection
URLs are resolved without serializing secret values in Git or the Application.
The chart also receives workshop, seat, session, tenant, and cluster identity
values and labels every resource with them.

The chart renders no Secret or cluster-scoped resource. An Arena server-side
dry run accepted all 21 rendered resources. The least-privilege rule in
`deploy/multicluster/arena-argocd-rbac.yaml` is applied: Arena verifies that the
remote Argo service account can create namespaced `ServiceMonitor` and DSPA
resources but cannot create cluster roles.

The repository now contains roughly 34 MiB of instructional images. The
adapted playbook uses the pinned PatternFly 6 Showroom theme; content delivery
therefore uses the same immutable Git-first path as the other Launchpad labs.

The namespace-scoped workload is now `gitops_ready: true`, while the catalog
item remains `draft` and capped at one seat. Arena now provides a functional
shared MLflow service backed by persistent PostgreSQL with verified OpenShift
service-ca TLS, plus a supported OpenShift Logging 6.6 one-seat pilot. The
participant can query application logs in the assigned namespace and is denied
access to another namespace. A Launchpad-created internal order has proven the
runtime Secret, workload Application, protected routes, Showroom, complete
participant journey, and zero-residue reclaim together. The next gate is
pipeline database TLS and production Logging storage, followed by the five-seat
functional and cleanup run. Five- and 25-seat promotion require durable
S3-compatible object storage, dynamic block storage, and a production-sized
Loki topology.
