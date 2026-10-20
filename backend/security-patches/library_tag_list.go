package registryclient

import (
	"context"

	"github.com/distribution/distribution/v3"
)

// List retains the authoritative source used by All. The maintained upstream
// client's List method is not implemented, so paginate its All result instead.
func (f blobMirroredTags) List(ctx context.Context, limit int, last string) ([]string, error) {
	var tags []string
	err := f.repo.source(ctx, func(r distribution.Repository) error {
		var err error
		tags, err = r.Tags(ctx).All(ctx)
		return err
	})
	if err != nil {
		return nil, err
	}
	return distribution.LegacyTagPage(tags, limit, last)
}
