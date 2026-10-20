#!/usr/bin/env bash
# Build-only source compatibility adapters. No cluster/registry credentials,
# publication, scanner policy, or vulnerability metadata are modified.
set -euo pipefail

patches="$(cd -- "$(dirname -- "$0")" && pwd)"
root="${CLIENT_MODULE_ROOT:-/tmp/launchpad-client-modules}"
mkdir "$root"
mkdir "$root/proof"
cache="$(go env GOMODCACHE)"
tests="${CLIENT_TEST_SOURCE:-/opt/launchpad-security-tests}"

fetch() {
  local module="$1" version="$2" sum="$3" report="$4"
  go mod download -json "$module@$version" > "$root/proof/$report"
  grep -F "\"Sum\": \"$sum\"" "$root/proof/$report"
}

fetch github.com/distribution/distribution/v3 "${GO_DISTRIBUTION_VERSION:?}" \
  'h1:u1v788HreKTLGdNY6s7px8Exgrs9mZ9UrCDjSrpCM8g=' distribution-upstream.json
legacy=v3.0.0-20230519140516-983358f8e250
fetch github.com/distribution/distribution/v3 "$legacy" \
  'h1:B3eXeuNArF23dRKyO8RXRiL7YAJDus6B7bjXeYPt87k=' distribution-legacy-upstream.json
fetch github.com/containers/image/v5 v5.36.2 \
  'h1:GcxYQyAHRF/pLqR4p4RpvKllnNL8mOBn0eZnqJbfTwk=' containers-image-upstream.json
library=v0.0.0-20260303171201-5d9eb6295ff6
fetch github.com/openshift/library-go "$library" \
  'h1:xjqy0OolrFdJ+ofI/aD0+2k9+MSk5anP5dXifFt539Q=' library-upstream.json
fetch github.com/fsouza/go-dockerclient "${GO_DOCKERCLIENT_VERSION:?}" \
  'h1:u+jAOuR9TZ3PAx2pdHA+ALt1ZZhS8Qx+A4d964IqXtw=' dockerclient-upstream.json

# Start with the real patched release. Only the removed legacy reference parser
# and schema-1 protocol helpers are restored; client/auth/transport facades call
# the maintained implementation in that release.
cp -a "$cache/github.com/distribution/distribution/v3@$GO_DISTRIBUTION_VERSION" "$root/distribution"
chmod -R u+w "$root/distribution"
cp -a "$cache/github.com/distribution/distribution/v3@$legacy/reference" "$root/distribution/reference"
cp -a "$cache/github.com/distribution/distribution/v3@$legacy/manifest/schema1" "$root/distribution/manifest/schema1"
chmod -R u+w "$root/distribution/reference" "$root/distribution/manifest/schema1"
go run -mod=mod "$patches/distribution_compat.go" "$root/distribution"
cp "$patches/distribution_legacy_api.go" "$root/distribution/launchpad_legacy_api.go"
git -C "$root/distribution" apply --check --unidiff-zero "$patches/distribution-reference-aliases.patch"
git -C "$root/distribution" apply --unidiff-zero "$patches/distribution-reference-aliases.patch"
git -C "$root/distribution" apply --check --unidiff-zero "$patches/distribution-schema1-tests.patch"
git -C "$root/distribution" apply --unidiff-zero "$patches/distribution-schema1-tests.patch"

# Preserve all legacy OpenPGP code. The only image-module source change replaces
# the deprecated Docker version-comparison import with the maintained equivalent.
cp -a "$cache/github.com/containers/image/v5@v5.36.2" "$root/image"
chmod -R u+w "$root/image"
git -C "$root/image" apply --check --unidiff-zero "$patches/image-sdk-split.patch"
git -C "$root/image" apply --unidiff-zero "$patches/image-sdk-split.patch"

# Module ZIPs omit the upstream fixture directory. Restore it from the exact
# verified source commit rather than skipping the legacy manifest test suite.
git clone --depth 1 --branch v5.36.2 https://github.com/containers/image.git "$root/image-fixtures"
test "$(git -C "$root/image-fixtures" rev-parse HEAD)" = d464a2540c2f0554dc27c268bfcfa181b2061ab3
git -C "$root/image-fixtures" rev-parse HEAD > "$root/proof/image-fixture-source.txt"
mkdir -p "$root/image/manifest/fixtures"
cp -RL "$root/image-fixtures/manifest/fixtures/." "$root/image/manifest/fixtures/"

cp -a "$cache/github.com/openshift/library-go@$library" "$root/library"
chmod -R u+w "$root/library"
cp "$patches/library_tag_list.go" "$root/library/pkg/image/registryclient/launchpad_tag_list.go"
cp "$patches/oc_file_tag_list.go" ./pkg/cli/image/imagesource/launchpad_tag_list.go
cp "$tests/distribution_legacy_api_test.go" "$root/distribution/launchpad_legacy_api_test.go"
cp "$tests/registry_client_protocol_test.go" "$root/library/pkg/image/registryclient/launchpad_protocol_test.go"

go mod edit \
  -require=github.com/fsouza/go-dockerclient@"$GO_DOCKERCLIENT_VERSION" \
  -require=github.com/distribution/distribution/v3@"$GO_DISTRIBUTION_VERSION" \
  -require=github.com/moby/moby/api@v1.56.1 \
  -require=github.com/moby/moby/client@v0.6.2 \
  -require=github.com/moby/sys/user@v0.4.1 \
  -replace=github.com/distribution/distribution/v3="$root/distribution" \
  -replace=github.com/containers/image/v5="$root/image" \
  -replace=github.com/openshift/library-go="$root/library"
sha256sum "$patches/prepare_client_modules.sh" \
  "$patches/distribution_compat.go" "$patches/distribution_legacy_api.go" \
  "$patches/distribution-reference-aliases.patch" "$patches/distribution-schema1-tests.patch" \
  "$patches/image-sdk-split.patch" "$patches/oc-sdk-split.patch" \
  "$patches/oc-newapp-unit-fixture.patch" \
  "$patches/library_tag_list.go" "$patches/oc_file_tag_list.go" \
  "$tests/distribution_legacy_api_test.go" "$tests/registry_client_protocol_test.go" \
  > "$root/proof/source-adapter-sha256.txt"
