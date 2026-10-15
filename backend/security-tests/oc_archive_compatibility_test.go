package archive

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"errors"
	"os"
	"path/filepath"
	"testing"
)

type launchpadAlter func(*tar.Header) (bool, error)

func (f launchpadAlter) Alter(h *tar.Header) (bool, error) { return f(h) }

func launchpadTar(t *testing.T, headers ...*tar.Header) []byte {
	t.Helper()
	var buf bytes.Buffer
	w := tar.NewWriter(&buf)
	for _, h := range headers {
		if err := w.WriteHeader(h); err != nil {
			t.Fatal(err)
		}
		if h.Typeflag == tar.TypeReg && h.Size > 0 {
			if _, err := w.Write(bytes.Repeat([]byte("x"), int(h.Size))); err != nil {
				t.Fatal(err)
			}
		}
	}
	if err := w.Close(); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}

func TestLaunchpadAlterHeadersPreservesSelectionAndRebase(t *testing.T) {
	root := t.TempDir()
	data := launchpadTar(t,
		&tar.Header{Name: "skip", Typeflag: tar.TypeReg, Mode: 0600, Size: 1},
		&tar.Header{Name: "source/keep", Typeflag: tar.TypeReg, Mode: 0600, Size: 3})
	opts := &TarOptions{Chown: false, AlterHeaders: launchpadAlter(func(h *tar.Header) (bool, error) {
		if h.Name == "skip" {
			return false, nil
		}
		h.Name = "rebased"
		return true, nil
	})}
	if _, err := ApplyLayer(root, bytes.NewReader(data), opts); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(root, "skip")); !os.IsNotExist(err) {
		t.Fatal("filtered entry created")
	}
	got, err := os.ReadFile(filepath.Join(root, "rebased"))
	if err != nil || string(got) != "xxx" {
		t.Fatalf("rebase/body lost: %q %v", got, err)
	}
}

func TestLaunchpadAlterHeaderErrorsPropagate(t *testing.T) {
	sentinel := errors.New("header rejected")
	data := launchpadTar(t, &tar.Header{Name: "entry", Typeflag: tar.TypeReg, Mode: 0600, Size: 1})
	_, err := ApplyLayer(t.TempDir(), bytes.NewReader(data), &TarOptions{
		AlterHeaders: launchpadAlter(func(*tar.Header) (bool, error) { return false, sentinel }),
	})
	if !errors.Is(err, sentinel) {
		t.Fatalf("lost header error: %v", err)
	}
}

func TestLaunchpadRebasedEscapeIsRejected(t *testing.T) {
	root := t.TempDir()
	dest := filepath.Join(root, "dest")
	if err := os.Mkdir(dest, 0700); err != nil {
		t.Fatal(err)
	}
	data := launchpadTar(t, &tar.Header{Name: "entry", Typeflag: tar.TypeReg, Mode: 0600, Size: 1})
	_, err := ApplyLayer(dest, bytes.NewReader(data), &TarOptions{
		AlterHeaders: launchpadAlter(func(h *tar.Header) (bool, error) { h.Name = "../outside"; return true, nil }),
	})
	if err == nil {
		t.Fatal("rebased escape accepted")
	}
	if _, err := os.Stat(filepath.Join(root, "outside")); !os.IsNotExist(err) {
		t.Fatal("rebased escape wrote outside destination")
	}
}

func TestLaunchpadPreservesLinksWhiteoutsAndCompressedInput(t *testing.T) {
	root := t.TempDir()
	if err := os.WriteFile(filepath.Join(root, "old"), []byte("old"), 0600); err != nil {
		t.Fatal(err)
	}
	data := launchpadTar(t,
		&tar.Header{Name: "file", Typeflag: tar.TypeReg, Mode: 0600, Size: 3},
		&tar.Header{Name: "hard", Typeflag: tar.TypeLink, Linkname: "file", Mode: 0600},
		&tar.Header{Name: "soft", Typeflag: tar.TypeSymlink, Linkname: "file", Mode: 0600},
		&tar.Header{Name: ".wh.old", Typeflag: tar.TypeReg, Mode: 0600})
	var compressed bytes.Buffer
	w := gzip.NewWriter(&compressed)
	if _, err := w.Write(data); err != nil {
		t.Fatal(err)
	}
	if err := w.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err := ApplyLayer(root, &compressed, &TarOptions{Chown: false}); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"file", "hard", "soft"} {
		got, err := os.ReadFile(filepath.Join(root, name))
		if err != nil || string(got) != "xxx" {
			t.Fatalf("%s: %q %v", name, got, err)
		}
	}
	if _, err := os.Stat(filepath.Join(root, "old")); !os.IsNotExist(err) {
		t.Fatal("whiteout did not remove old file")
	}
}

func TestLaunchpadRejectsHardlinkWriteThroughPreexistingEscape(t *testing.T) {
	root := t.TempDir()
	dest := filepath.Join(root, "dest")
	outside := filepath.Join(root, "outside")
	if err := os.Mkdir(dest, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(outside, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(dest, "link")); err != nil {
		t.Fatal(err)
	}
	data := launchpadTar(t,
		&tar.Header{Name: "copy", Typeflag: tar.TypeLink, Linkname: "link", Mode: 0600},
		&tar.Header{Name: "copy/proof", Typeflag: tar.TypeReg, Mode: 0600, Size: 1})
	if _, err := ApplyLayer(dest, bytes.NewReader(data), &TarOptions{Chown: false}); err == nil {
		t.Fatal("write through escaping hardlink accepted")
	}
	if _, err := os.Stat(filepath.Join(outside, "proof")); !os.IsNotExist(err) {
		t.Fatal("archive wrote outside extraction root through a hardlink")
	}
}

func TestLaunchpadRejectsParentCreationOutsideRootBeforeMutation(t *testing.T) {
	root := t.TempDir()
	dest := filepath.Join(root, "dest")
	if err := os.Mkdir(dest, 0700); err != nil {
		t.Fatal(err)
	}
	data := launchpadTar(t, &tar.Header{
		Name: "../outside/new-parent/proof", Typeflag: tar.TypeReg, Mode: 0600, Size: 1,
	})
	if _, err := ApplyLayer(dest, bytes.NewReader(data), &TarOptions{Chown: false}); err == nil {
		t.Fatal("traversing entry accepted")
	}
	if _, err := os.Stat(filepath.Join(root, "outside")); !os.IsNotExist(err) {
		t.Fatal("archive created parent directories outside extraction root before rejecting the entry")
	}
}
