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

## 1. Read the digest the run published

```bash
RUN=45713500003            # the publish run, not the measurement run
SHA=e691b6b2b66108657b825660a83c5796b01b415b

gh run download "$RUN" --repo rhpds/launchpad -n "terminal-release-$SHA" -D /tmp/terminal-release
cat /tmp/terminal-release/terminal-release.json
```

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

## 6. Apply the live config and roll

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
oc -n launchpad-flightpath-candidate apply -f /tmp/cluster-targets.yaml
oc -n launchpad-flightpath-candidate rollout status deploy/backend --timeout=300s
```

`cluster-targets` is a directory mount (no `subPath`), so the file does update
in place — but the adapter reads cluster targets at startup, so the rollout is
what actually changes behaviour.

Verify the mounted file, not the ConfigMap:

```bash
POD=$(oc -n launchpad-flightpath-candidate get pod -l app=backend -o name | head -1)
oc -n launchpad-flightpath-candidate exec "$POD" -- \
  grep showroom_terminal /etc/launchpad/clusters.yaml
```

## 7. Prove a participant gets that image

Place one public, one-seat order against a catalog item that declares
`showroom_terminal_storage`, then read the seat pod rather than the order:

```bash
oc get pods -A -o json | jq -r '.items[]
  | select(.spec.containers[0].image|test("launchpad-showroom-terminal"))
  | "\(.metadata.namespace)  \(.spec.containers[0].image)"'
```

Every terminal pod must show `quay.io/rh-ee-jkershaw/launchpad-showroom-terminal@sha256:<digest>`.

## 8. Record it

Write `evidence/runs/terminal-promotion-<date>.json` with the release run id,
the GHCR digest, the Quay digest, the equality of the two, the repinned files
and the seat-pod observation. A promotion nobody can audit is indistinguishable
from an inconsistent one.
