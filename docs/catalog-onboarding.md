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

`agentops-observability` is registered as a draft candidate from:

- Showroom: `rhpds/agentops-intel-showroom` at
  `f1881c61de55ebf5640c27e76469f4efe458edaf`;
- workload: `rh-ai-quickstart/multi-agent-loan-origination` at
  `1e50e51c334c1b6ed854d81a3f28fd324792f481`.

Its source and Antora build pass. It is not orderable because the Showroom
expects a pre-provisioned mortgage application, MLflow, Grafana, OpenShift
Logging, user workload monitoring, OpenShift AI workbenches/pipelines, a model,
and six environment tabs. The upstream workload is a Helm chart, but Launchpad
does not yet have the per-seat Helm adapter and functional validators required
to own that lifecycle safely. Its default render also creates a cluster-wide
MLflow role and binding plus one Keycloak deployment per seat; both must be
replaced by shared, least-privilege platform integration before activation. The
source contains roughly 34 MiB of instructional images and references a mutable
`latest` Showroom theme, so content delivery and theme pinning are also explicit
activation gates rather than hidden per-seat download costs.
