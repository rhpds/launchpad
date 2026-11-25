# Terminal image promotion runbook — 2026-11-25

How the signed terminal digest gets from the build to the image Flightpath
actually runs, and how to prove it arrived unchanged.

**What this changes:** one digest in `launchpad-cluster-targets` and two
overlay files (plus the two tests that pin them).

**What this deliberately does not change:** the provisioner's pull-grant
boundary. `_requires_image_pull_grant`
(`backend/app/adapters/openshift/provisioning.py:1502`) declines to bind an
internal pull grant only when every showroom support image matches
`quay.io/…@sha256:…`. Promoting into the existing Quay repository keeps that
invariant, its test, and `config/artifact-registry-policy.yaml` untouched.

## Why a copy at all

`terminal-release.yml` publishes to `ghcr.io/rhpds/launchpad-showroom-terminal`,
because that is what `IMAGE_REPOSITORY` derives from `github.repository_owner`
and it is where the workflow's cosign identity and provenance attestation are
valid. The overlays and the live cluster target pin
`quay.io/rh-ee-jkershaw/launchpad-showroom-terminal`. Something has to move the
image between them, and it must preserve the manifest digest: a re-serialised
manifest is a different digest, which the signature does not cover and the
risk acceptance does not name.

## Preconditions

1. A `terminal-release.yml` run with `publish: true` completed green. The gate
   decision must read `PASS-SCAN-ONLY` / `risk_acceptance: GRANTED` /
   `gate_basis: SIGNED-ACCEPTANCE`; `BLOCKED` means stop and re-render.
2. You have push access to `quay.io/rh-ee-jkershaw/launchpad-showroom-terminal`.
3. `podman` works locally. `skopeo` is not installed on this Mac, so the copy
   runs from the upstream skopeo container image.
4. The target cluster has capacity to admit one seat under the workshop
   headroom policy. A correct digest does not imply an admitted order; see
   step 7.

## 1. Read the digest the run published

```bash
RUN=45721636396            # the publish run, not a measurement run
SHA=e26a87c39894c2ef8b64ea7ba2b19179300d3290   # expected_sha, not the branch tip

gh run download "$RUN" --repo rhpds/launchpad -n "terminal-release-$SHA" -D /tmp/terminal-release
cat /tmp/terminal-release/terminal-release.json
```

Take the revision from the run's `expected_sha` input, not from the branch tip:
the run is dispatched at the branch tip but checks out and releases
`expected_sha`, and the artifact name carries that SHA. For the 2026-11-25
release the branch tip was `cb7c8839` (the commit holding the signed record)
while the released revision was `e26a87c3`.

`RUN=45713500003` and `SHA=e691b6b2…` appear in some notes as the publish run;
they are a **failed** run that exited `2` (`INVALID`) on the containerd/docker
identity mismatch. A run that ends `INVALID` produced no digest to promote, so
never copy `--all` from one.

Expected shape:

```json
{"schema_version":"launchpad.redhat.com/terminal-release/v1",
 "source_revision":"<sha>",
 "image":"ghcr.io/rhpds/launchpad-showroom-terminal@sha256:<digest>",
 "image_id":"sha256:<config-digest>",
 "platform":"linux/amd64","published":true}
```

The workflow has already asserted, before signing, that `image_id` is the same
image ID the security gate scanned. That assertion is the only thing that makes
a `digest_pending` acceptance honest — do not promote a digest that lacks it.

## 2. Copy it into Quay, preserving the digest

```bash
SRC="ghcr.io/rhpds/launchpad-showroom-terminal@sha256:<digest>"
DST="quay.io/rh-ee-jkershaw/launchpad-showroom-terminal:git-<short-sha>"

podman run --rm \
  -v "$HOME/.config/containers/auth.json:/auth.json:ro" \
  quay.io/skopeo/stable:latest copy --all --authfile /auth.json \
  "docker://$SRC" "docker://$DST"
```

`--all` keeps every manifest in the index rather than resolving to this
architecture, which is what keeps the digest identical.

## 3. Prove the digest survived

```bash
podman run --rm quay.io/skopeo/stable:latest \
  inspect --format '{{.Digest}}' \
  "docker://quay.io/rh-ee-jkershaw/launchpad-showroom-terminal:git-<short-sha>"
```

This must print `sha256:<digest>` — byte-for-byte the value from
`terminal-release.json`. **If it differs, stop.** A different digest is a
different artifact: the GHCR signature does not cover it, the acceptance does
not name it, and repinning it would ship an unreviewed image.

## 4. Check the signature where it actually lives

```bash
cosign verify \
  --certificate-identity="https://github.com/rhpds/launchpad/.github/workflows/terminal-release.yml@refs/heads/codex/flightpath-migration-20260922" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  "ghcr.io/rhpds/launchpad-showroom-terminal@sha256:<digest>"
```

Verify against GHCR. `skopeo copy --all` does not carry cosign's `.sig` tag, so
verifying against Quay fails for a reason that says nothing about the image.
What makes the Quay copy trustworthy is step 3: identical digest, therefore
identical content, therefore the same signature applies.

## 5. Repin, in this order

| File | Why it moves |
|---|---|
| `deploy/launchpad/overlays/flightpath-candidate/candidate-clusters.yaml` | the rendered `launchpad-cluster-targets` |
| `deploy/launchpad/overlays/arena/arena-clusters.yaml` | the Arena overlay pins the same repository |
| `backend/tests/test_multicluster.py` | asserts the pinned digest |
| `scripts/tests/test_flightpath_candidate_overlay.py` | asserts the overlay digest |

Then:

```bash
PYTHONPATH=. pytest backend/tests/test_multicluster.py scripts/tests/test_flightpath_candidate_overlay.py backend/tests/test_openshift_image_pull_grant.py -q
```

`test_deployed_cluster_images_and_pilot_catalog_preserve_grant_boundary` must
still pass: the image stays under `quay.io/…@sha256:…`, so Flightpath still
needs no internal pull grant.

## 6. Apply the live config and **restart** the backend

```bash
export KUBECONFIG=~/.kube/config-flightpath
oc kustomize deploy/launchpad/overlays/flightpath-candidate > /tmp/rendered.yaml
# replace only launchpad-cluster-targets; do not apply unrelated catalog drift
python3 - <<'PY'
import yaml
docs=[d for d in yaml.safe_load_all(open('/tmp/rendered.yaml')) if d]
cm=[d for d in docs if d.get('kind')=='ConfigMap' and d['metadata']['name']=='launchpad-cluster-targets']
yaml.safe_dump(cm[0], open('/tmp/cluster-targets.yaml','w'))
print('wrote', cm[0]['metadata']['name'])
PY
```

Diff the render against the live ConfigMap before applying, so the change you
review is the change you ship:

```bash
diff <(oc -n launchpad-flightpath-candidate get cm launchpad-cluster-targets \
        -o jsonpath='{.data.clusters\.yaml}') \
     <(python3 -c "import yaml;print(yaml.safe_load(open('/tmp/cluster-targets.yaml'))['data']['clusters.yaml'],end='')")
```

For the 2026-11-25 promotion this differed in exactly one line: the
`showroom_terminal` digest. Anything else in the diff is unrelated drift and
must not ride along.

```bash
oc -n launchpad-flightpath-candidate apply -f /tmp/cluster-targets.yaml
oc -n launchpad-flightpath-candidate rollout restart deploy/backend
oc -n launchpad-flightpath-candidate rollout status deploy/backend --timeout=420s
```

**`oc rollout status` immediately after an `apply` is a false green.** A
ConfigMap is not part of the Deployment's pod template, so `apply` does not
create a new ReplicaSet, `generation` does not change, and `rollout status`
reports the *old* pod as successfully rolled out. The adapter reads cluster
targets at startup, so without `rollout restart` the backend keeps serving the
old digest indefinitely — this actually happened on 2026-11-25 (generation 382
unchanged, a 22h-old pod still mounting the previous digest). After the restart
`generation` must increment and the pod age must reset.

Verify the mounted file in the **new** pod, not the ConfigMap. The selector is
`app.kubernetes.io/name=backend`, not `app=backend`, and the container is named
`backend` (`oauth-proxy` is the second container):

```bash
POD=$(oc -n launchpad-flightpath-candidate get pod \
        -l app.kubernetes.io/name=backend -o name | head -1)
oc -n launchpad-flightpath-candidate exec "$POD" -c backend -- \
  grep showroom_terminal /etc/launchpad/clusters.yaml
```

## 7. Prove a participant gets that image

Admission is not guaranteed by a correct pin. A one-seat order only provisions
if the capacity gate admits it, so check that first:

```bash
curl -s -X POST http://127.0.0.1:18000/api/v1/workshops/capacity-preview \
  -H "X-API-Key: $ADMIN_KEY" -H 'Content-Type: application/json' \
  --data '{"tenant_id":"flightpath-candidate-cert","catalog_item_id":"virtualization-ai-201",
           "num_users":1,"ttl":"10m","target_cluster":"flightpath","exposure_policy":"public_code"}'
```

`can_provision: false` means the order will be created `failed` and no seat pod
will ever exist — which is a capacity answer, not an image answer. On
2026-11-25 this returned `false` with `CPU: 0`, because the three eligible
workers carried 681 784 m of requests against a 606 912 m budget (80 % of
758 640 m allocatable). The order still failed closed, which is the correct
behaviour but proves nothing about the terminal.

Then place one public, one-seat order against a catalog item that declares
`showroom_terminal_storage`, and read the seat pod rather than the order:

```bash
oc get pods -A -o json | jq -r '.items[]
  | select(.spec.containers[0].image|test("launchpad-showroom-terminal"))
  | "\(.metadata.namespace)  \(.spec.containers[0].image)"'
```

Every terminal pod must show `quay.io/rh-ee-jkershaw/launchpad-showroom-terminal@sha256:<digest>`.
A cluster with zero terminal pods proves nothing either: capture the post-order
observation, not the baseline.

## 8. Record it

Write `evidence/runs/terminal-promotion-<date>.json` with the release run id,
the GHCR digest, the Quay digest, the equality of the two, the repinned files
and the seat-pod observation. A promotion nobody can audit is indistinguishable
from an inconsistent one.
