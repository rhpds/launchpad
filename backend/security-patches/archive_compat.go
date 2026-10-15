package archive

import "github.com/moby/go-archive/compression"

// Compression preserves the deprecated type alias consumed by Docker 28's
// compatibility wrapper. It does not alter the root-confined extraction code.
type Compression = compression.Compression
