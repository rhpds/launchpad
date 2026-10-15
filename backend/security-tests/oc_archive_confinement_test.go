package archive

import (
	"archive/tar"
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

// All writes, including the attempted escape, remain inside t.TempDir().
func TestLaunchpadArchiveRejectsSiblingPrefixEscape(t *testing.T) {
	root := t.TempDir()
	dest := filepath.Join(root, "extract")
	outside := filepath.Join(root, "extract-outside")
	for _, dir := range []string{dest, outside} {
		if err := os.Mkdir(dir, 0700); err != nil {
			t.Fatal(err)
		}
	}
	var buf bytes.Buffer
	tw := tar.NewWriter(&buf)
	headers := []*tar.Header{
		{Name: "escape", Typeflag: tar.TypeSymlink, Linkname: "../extract-outside", Mode: 0700},
		{Name: "escape/proof.txt", Typeflag: tar.TypeReg, Size: 5, Mode: 0600},
	}
	for _, h := range headers {
		if err := tw.WriteHeader(h); err != nil {
			t.Fatal(err)
		}
		if h.Typeflag == tar.TypeReg {
			if _, err := tw.Write([]byte("proof")); err != nil {
				t.Fatal(err)
			}
		}
	}
	if err := tw.Close(); err != nil {
		t.Fatal(err)
	}
	_, err := ApplyLayer(dest, bytes.NewReader(buf.Bytes()), &TarOptions{Chown: false})
	if _, statErr := os.Stat(filepath.Join(outside, "proof.txt")); statErr == nil {
		t.Fatalf("archive wrote outside extraction directory (within disposable test root); extraction error: %v", err)
	} else if !os.IsNotExist(statErr) {
		t.Fatal(statErr)
	}
	if err == nil {
		t.Fatal("crafted archive must be rejected")
	}
}

func TestLaunchpadArchiveRejectsPreexistingSymlinkEscape(t *testing.T) {
	root := t.TempDir()
	dest := filepath.Join(root, "extract")
	outside := filepath.Join(root, "outside")
	for _, dir := range []string{dest, outside} {
		if err := os.Mkdir(dir, 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.Symlink(outside, filepath.Join(dest, "escape")); err != nil {
		t.Fatal(err)
	}
	var buf bytes.Buffer
	tw := tar.NewWriter(&buf)
	if err := tw.WriteHeader(&tar.Header{Name: "escape/proof.txt", Typeflag: tar.TypeReg, Size: 5, Mode: 0600}); err != nil {
		t.Fatal(err)
	}
	if _, err := tw.Write([]byte("proof")); err != nil {
		t.Fatal(err)
	}
	if err := tw.Close(); err != nil {
		t.Fatal(err)
	}
	_, err := ApplyLayer(dest, bytes.NewReader(buf.Bytes()), &TarOptions{Chown: false})
	if _, statErr := os.Stat(filepath.Join(outside, "proof.txt")); statErr == nil {
		t.Fatalf("preexisting symlink escaped extraction root within disposable directory; extraction error: %v", err)
	} else if !os.IsNotExist(statErr) {
		t.Fatal(statErr)
	}
	if err == nil {
		t.Fatal("escaping symlink must be rejected")
	}
}

func TestLaunchpadArchivePreservesOrdinaryExtraction(t *testing.T) {
	dest := t.TempDir()
	var buf bytes.Buffer
	tw := tar.NewWriter(&buf)
	if err := tw.WriteHeader(&tar.Header{Name: "proof.txt", Typeflag: tar.TypeReg, Size: 5, Mode: 0600}); err != nil {
		t.Fatal(err)
	}
	if _, err := tw.Write([]byte("proof")); err != nil {
		t.Fatal(err)
	}
	if err := tw.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err := ApplyLayer(dest, bytes.NewReader(buf.Bytes()), &TarOptions{Chown: false}); err != nil {
		t.Fatal(err)
	}
	actual, err := os.ReadFile(filepath.Join(dest, "proof.txt"))
	if err != nil || string(actual) != "proof" {
		t.Fatalf("ordinary extraction failed: %q %v", actual, err)
	}
}
