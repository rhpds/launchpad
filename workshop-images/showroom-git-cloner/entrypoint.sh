#!/bin/bash

set -euo pipefail

export GIT_TERMINAL_PROMPT=0
export GIT_CONFIG_GLOBAL=/tmp/.gitconfig

: "${GIT_REPO_URL:?Error: GIT_REPO_URL environment variable is not set or empty.}"

CLONE_DIR="${CLONE_DIR:-/files}"
GIT_REPO_REF="${GIT_REPO_REF:-}"

if [[ -d "${CLONE_DIR}" ]]; then
    rm -f "${CLONE_DIR}/.git-cloner"
    find "${CLONE_DIR}" -mindepth 1 -delete
fi

echo "Cloning ${GIT_REPO_URL} into ${CLONE_DIR}"

clone_args=(clone --progress)
checkout_sha=false
if [[ -n "${GIT_REPO_REF}" ]]; then
    if [[ "${GIT_REPO_REF}" =~ ^[0-9a-fA-F]{7,40}$ ]]; then
        checkout_sha=true
    else
        clone_args+=(--single-branch --branch "${GIT_REPO_REF}")
    fi
else
    clone_args+=(--single-branch)
fi
clone_args+=("${GIT_REPO_URL}" "${CLONE_DIR}")

clone_success=false
for attempt in {1..10}; do
    if git "${clone_args[@]}"; then
        clone_success=true
        break
    fi
    echo "Clone attempt ${attempt} failed; retrying in 10 seconds"
    sleep 10
done
[[ "${clone_success}" == true ]] || exit 1

# OpenShift may assign the pod a supplemental group that owns the emptyDir.
# Mark the repository safe before entering it or running any repository-aware
# command; doing this after cd causes Git 2.35+ to reject the repository.
git config --global --add safe.directory "${CLONE_DIR}"

if [[ "${checkout_sha}" == true ]]; then
    git -C "${CLONE_DIR}" checkout "${GIT_REPO_REF}"
fi

cd "${CLONE_DIR}"
touch .git-cloner

echo "Repository clone completed"
