// Legacy schema-1 builder contract retained for the OpenShift client adapter.
// The patched Distribution server and maintained registry client stay unchanged.
package distribution

import (
	"context"
	"fmt"
	"sort"
)

type ManifestBuilder interface {
	Build(context.Context) (Manifest, error)
	References() []Descriptor
	AppendReference(Describable) error
}

// LegacyDescriptor restores the historical Describable adapter without changing
// the maintained OCI descriptor representation or the server's manifest handling.
type LegacyDescriptor Descriptor

func (d LegacyDescriptor) Descriptor() Descriptor { return Descriptor(d) }

// LegacyTagPage paginates a copy of the existing All result. The maintained
// Distribution client has no List implementation, so do not call that panic path.
func LegacyTagPage(tags []string, limit int, last string) ([]string, error) {
	if limit < 0 {
		return nil, fmt.Errorf("tag page limit must not be negative")
	}
	page := append([]string(nil), tags...)
	sort.Strings(page)
	start := sort.Search(len(page), func(i int) bool { return page[i] > last })
	page = page[start:]
	if limit > 0 && len(page) > limit {
		page = page[:limit]
	}
	return page, nil
}
