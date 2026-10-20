package distribution

import (
	"reflect"
	"testing"

	"github.com/opencontainers/go-digest"
)

func TestLaunchpadLegacyTagPagination(t *testing.T) {
	input := []string{"z", "a", "m"}
	for _, tc := range []struct {
		name  string
		limit int
		last  string
		want  []string
	}{
		{"all", 0, "", []string{"a", "m", "z"}},
		{"first", 1, "", []string{"a"}},
		{"after", 1, "a", []string{"m"}},
		{"gap", 5, "b", []string{"m", "z"}},
		{"end", 5, "z", []string{}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got, err := LegacyTagPage(input, tc.limit, tc.last)
			if err != nil || !reflect.DeepEqual(got, tc.want) {
				t.Fatalf("page=%v error=%v want=%v", got, err, tc.want)
			}
			if !reflect.DeepEqual(input, []string{"z", "a", "m"}) {
				t.Fatal("pagination changed the source tag cache")
			}
		})
	}
	if _, err := LegacyTagPage(input, -1, ""); err == nil {
		t.Fatal("negative page size accepted")
	}
}

func TestLaunchpadLegacyDescriptorPreservesManifestIdentity(t *testing.T) {
	want := Descriptor{Digest: digest.FromString("legacy manifest"), Size: 42,
		MediaType:   "application/vnd.docker.distribution.manifest.v1+json",
		Annotations: map[string]string{"purpose": "compatibility-test"}}
	var describable Describable = LegacyDescriptor(want)
	if !reflect.DeepEqual(describable.Descriptor(), want) {
		t.Fatal("descriptor adapter changed manifest identity or metadata")
	}
}
