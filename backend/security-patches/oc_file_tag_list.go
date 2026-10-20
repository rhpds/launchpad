package imagesource

import (
	"context"

	"github.com/distribution/distribution/v3"
)

func (s *fileTagStore) List(ctx context.Context, limit int, last string) ([]string, error) {
	tags, err := s.All(ctx)
	if err != nil {
		return nil, err
	}
	return distribution.LegacyTagPage(tags, limit, last)
}
