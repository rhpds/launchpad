#!/usr/bin/env bash
# Refresh the embedded learner CLIs with immutable, checksum-pinned vendor
# artifacts so the complete-image security gate can evaluate current builds.
#
# Sourcing rules (see evidence/convergence/terminal-os-refresh-20261015.yaml):
#   - Every downloaded artifact is verified against a pinned SHA256 before it
#     replaces the inherited base-image binary.
#   - Checksums for helm, tkn, tkn-pac and opc match the vendor-published
#     checksum files; kn, oc/kubectl and roxctl pins were computed from the
#     exact vendor artifacts referenced below.
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
verify \
  "https://get.helm.sh/helm-v3.22.1-linux-amd64.tar.gz" \
  "896cf63684a42a723d61c980369d6e588330927deb13676ca0d85006dd6da0ea" \
  /tmp/helm-v3.22.1-linux-amd64.tar.gz
tar -xzf /tmp/helm-v3.22.1-linux-amd64.tar.gz -C /tmp linux-amd64/helm
install -m 0755 /tmp/linux-amd64/helm /usr/local/bin/helm

# oc + kubectl 4.22.18 from the OpenShift client mirror bundle. The bundle
# ships the oc binary for both names, matching the inherited base-image
# layout, so learner commands keep their existing behavior.
verify \
  "https://mirror.openshift.com/pub/openshift-v4/amd64/clients/ocp/4.22.18/openshift-client-linux-4.22.18.tar.gz" \
  "07751676809553e012448cdb3a755ffa7b11d7e25b8a6cc60a5a62a9f4b18159" \
  /tmp/openshift-client-linux-4.22.18.tar.gz
tar -xzf /tmp/openshift-client-linux-4.22.18.tar.gz -C /tmp oc kubectl
install -m 0755 /tmp/oc /usr/local/bin/oc
install -m 0755 /tmp/kubectl /usr/local/bin/kubectl

# kn v1.23.0 (knative client)
verify \
  "https://github.com/knative/client/releases/download/knative-v1.23.0/kn-linux-amd64" \
  "852a3229e3e36e69a7f006da882f7841138fc39047051589841f24336d8f37b2" \
  /tmp/kn-linux-amd64
install -m 0755 /tmp/kn-linux-amd64 /usr/local/bin/kn

# tkn v0.46.1 (official checksums.txt)
verify \
  "https://github.com/tektoncd/cli/releases/download/v0.46.1/tkn_0.46.1_Linux_x86_64.tar.gz" \
  "bc9fe51595af87cee422ae19a62ab46c8cdcb0a74f7157ffa8b9a9ef39b3d390" \
  /tmp/tkn-v0.46.1-linux-x86_64.tar.gz
tar -xzf /tmp/tkn-v0.46.1-linux-x86_64.tar.gz -C /tmp tkn
install -m 0755 /tmp/tkn /usr/local/bin/tkn

# tkn-pac v0.52.0 (official checksums.txt)
verify \
  "https://github.com/openshift-pipelines/pipelines-as-code/releases/download/v0.52.0/tkn-pac_0.52.0_linux_x86_64.tar.gz" \
  "943d8da4393d997154a9dd723e754ecc4daa3797df44f7a1c3f4a6b893c32cba" \
  /tmp/tkn-pac-v0.52.0-linux-x86_64.tar.gz
tar -xzf /tmp/tkn-pac-v0.52.0-linux-x86_64.tar.gz -C /tmp tkn-pac
install -m 0755 /tmp/tkn-pac /usr/local/bin/tkn-pac

# opc v1.24.0 (official checksums.txt)
verify \
  "https://github.com/openshift-pipelines/opc/releases/download/v1.24.0/opc_1.24.0_linux_x86_64.tar.gz" \
  "4ad40ad3204dad203e2dadc0f5e79adfb2953f122b2e036e96e4bacd51090930" \
  /tmp/opc-v1.24.0-linux-x86_64.tar.gz
tar -xzf /tmp/opc-v1.24.0-linux-x86_64.tar.gz -C /tmp opc
install -m 0755 /tmp/opc /usr/local/bin/opc

# roxctl 4.11.5 (RHACS client mirror)
verify \
  "https://mirror.openshift.com/pub/rhacs/assets/4.11.5/bin/linux/roxctl" \
  "5c7e604b6672354a79d0a3d3e1cda363618f89a6a38353a2a94445b6eab703bb" \
  /tmp/roxctl-4.11.5
install -m 0755 /tmp/roxctl-4.11.5 /usr/local/bin/roxctl

# Remove every downloaded and extracted staging artifact so the complete-image
# scan evaluates exactly one copy of each learner CLI and the published image
# carries no duplicate binaries.
rm -f /tmp/helm-v3.22.1-linux-amd64.tar.gz \
  /tmp/openshift-client-linux-4.22.18.tar.gz \
  /tmp/tkn-v0.46.1-linux-x86_64.tar.gz \
  /tmp/tkn-pac-v0.52.0-linux-x86_64.tar.gz \
  /tmp/opc-v1.24.0-linux-x86_64.tar.gz \
  /tmp/kn-linux-amd64 /tmp/roxctl-4.11.5 \
  /tmp/oc /tmp/kubectl /tmp/tkn /tmp/tkn-pac /tmp/opc /tmp/helm
rm -rf /tmp/linux-amd64

# odo: REMOVED with owner authorization on 2026-10-16. Upstream is at its
# terminal v3.16.1 release with no fixed artifact available, and no lab
# content references the tool. See the sourcing note at the top of this file
# for the rationale and the documented restore path.
rm -f /usr/local/bin/odo
