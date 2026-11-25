#!/usr/bin/env bash
# Refresh the embedded learner CLIs with immutable, checksum-pinned vendor
# artifacts so the complete-image security gate can evaluate current builds.
#
# Sourcing rules (see evidence/convergence/terminal-os-refresh-20261015.yaml):
#   - Every downloaded artifact is verified against a pinned SHA256 before it
#     replaces the inherited base-image binary.
#   - Every checksum below is transcribed from a vendor-published checksum
#     file: helm's .sha256sum, the Tekton and Pipelines-as-Code checksums.txt
#     assets, knative's checksums.txt, and the OpenShift client and RHACS
#     mirror sha256sum.txt files.
#   - skopeo v1.24.1 is built from the immutable upstream source tag inside
#     the Containerfile (pinned Go toolchain + checksum-pinned source tarball)
#     because skopeo publishes no release binaries and the vendor container
#     image targets an incompatible glibc.
#   - odo is REMOVED with owner authorization (2026-10-16): upstream
#     redhat-developer/odo and the Red Hat mirror both ended at v3.16.1
#     (built with go1.21.10), no fixed artifact exists, and no lab content
#     references the tool. It carried 21 Critical + 106 High fixable findings
#     in the complete-image scan. Restore path: re-add a pinned vendor or
#     source-built odo when a fixed release exists or lab content requires it.
#   - No other tool is stripped, no failure is ignored, and no security
#     exception is introduced by this script.
set -euo pipefail

verify() {
  local url="$1" sha="$2" dest="$3"
  curl --fail --silent --show-error --location --retry 5 --retry-all-errors \
    "$url" --output "$dest"
  printf '%s  %s\n' "$sha" "$dest" | sha256sum --check -
}

# helm v3.22.1 (official checksum: helm-v3.22.1-linux-amd64.tar.gz.sha256sum)
# Deliberately NOT moved to 4.3.2: 3.22.1 already scans 0 Critical / 0 High, so
# the v4 major-version behaviour change buys no security and risks lab content.
verify \
  "https://get.helm.sh/helm-v3.22.1-linux-amd64.tar.gz" \
  "896cf63684a42a723d61c980369d6e588330927deb13676ca0d85006dd6da0ea" \
  /tmp/helm-v3.22.1-linux-amd64.tar.gz
tar -xzf /tmp/helm-v3.22.1-linux-amd64.tar.gz -C /tmp linux-amd64/helm
install -m 0755 /tmp/linux-amd64/helm /usr/local/bin/helm

# oc + kubectl 4.22.23 from the OpenShift client mirror bundle. The bundle
# ships the oc binary for both names, matching the inherited base-image
# layout, so learner commands keep their existing behavior.
# 4.22.23 is the first client build carrying go1.26.10; 4.22.18/4.22.22 were
# both go1.25.14 and contributed three Critical stdlib advisories each.
verify \
  "https://mirror.openshift.com/pub/openshift-v4/amd64/clients/ocp/4.22.23/openshift-client-linux-4.22.23.tar.gz" \
  "053507b991867cb04a172a36e4ca7edd935fa2e5909b03a0b8392807991f89ae" \
  /tmp/openshift-client-linux-4.22.23.tar.gz
tar -xzf /tmp/openshift-client-linux-4.22.23.tar.gz -C /tmp oc kubectl
install -m 0755 /tmp/oc /usr/local/bin/oc
install -m 0755 /tmp/kubectl /usr/local/bin/kubectl

# kn v1.24.0 (knative client; checksums.txt asset)
verify \
  "https://github.com/knative/client/releases/download/knative-v1.24.0/kn-linux-amd64" \
  "7a69805deda57ff45e3f48aac5d1b0f0b258bc3a85ec2d033770a6e3d38af777" \
  /tmp/kn-linux-amd64
install -m 0755 /tmp/kn-linux-amd64 /usr/local/bin/kn

# tkn v0.47.0 (official checksums.txt)
verify \
  "https://github.com/tektoncd/cli/releases/download/v0.47.0/tkn_0.47.0_Linux_x86_64.tar.gz" \
  "ea027194967eb010fee9d942cf021512e9a924660ff6b31bb6012926868198f8" \
  /tmp/tkn-v0.47.0-linux-x86_64.tar.gz
tar -xzf /tmp/tkn-v0.47.0-linux-x86_64.tar.gz -C /tmp tkn
install -m 0755 /tmp/tkn /usr/local/bin/tkn

# tkn-pac v0.54.0 (official checksums.txt)
verify \
  "https://github.com/openshift-pipelines/pipelines-as-code/releases/download/v0.54.0/tkn-pac_0.54.0_linux_x86_64.tar.gz" \
  "fcc8ebdf15ded61720d44ec03602be12664754de9aa6fd17868858e43c2752bf" \
  /tmp/tkn-pac-v0.54.0-linux-x86_64.tar.gz
tar -xzf /tmp/tkn-pac-v0.54.0-linux-x86_64.tar.gz -C /tmp tkn-pac
install -m 0755 /tmp/tkn-pac /usr/local/bin/tkn-pac

# opc v1.25.0 (official checksums.txt)
verify \
  "https://github.com/openshift-pipelines/opc/releases/download/v1.25.0/opc_1.25.0_linux_x86_64.tar.gz" \
  "1e90aba71b440a4a57cb8fff7eeb5ada64057cfb7e5dc86c45e5a0bd5b807e5a" \
  /tmp/opc-v1.25.0-linux-x86_64.tar.gz
tar -xzf /tmp/opc-v1.25.0-linux-x86_64.tar.gz -C /tmp opc
install -m 0755 /tmp/opc /usr/local/bin/opc

# roxctl 5.0.0 (RHACS client mirror; sha256sum.txt). 5.0.0 drops the
# github.com/containerd/containerd dependency entirely, which removes the two
# Critical containerd advisories that 4.11.5 could not fix.
verify \
  "https://mirror.openshift.com/pub/rhacs/assets/5.0.0/bin/linux/roxctl" \
  "b29c432b7b0e40719969ae3d9e4e202559dce6a746e5b9a62eefcd3bb788fd6b" \
  /tmp/roxctl-5.0.0
install -m 0755 /tmp/roxctl-5.0.0 /usr/local/bin/roxctl

# Remove every downloaded and extracted staging artifact so the complete-image
# scan evaluates exactly one copy of each learner CLI and the published image
# carries no duplicate binaries.
rm -f /tmp/helm-v3.22.1-linux-amd64.tar.gz \
  /tmp/openshift-client-linux-4.22.23.tar.gz \
  /tmp/tkn-v0.47.0-linux-x86_64.tar.gz \
  /tmp/tkn-pac-v0.54.0-linux-x86_64.tar.gz \
  /tmp/opc-v1.25.0-linux-x86_64.tar.gz \
  /tmp/kn-linux-amd64 /tmp/roxctl-5.0.0 \
  /tmp/oc /tmp/kubectl /tmp/tkn /tmp/tkn-pac /tmp/opc /tmp/helm
rm -rf /tmp/linux-amd64

# odo: REMOVED with owner authorization on 2026-10-16. Upstream is at its
# terminal v3.16.1 release with no fixed artifact available, and no lab
# content references the tool. See the sourcing note at the top of this file
# for the rationale and the documented restore path.
rm -f /usr/local/bin/odo
