package registryclient

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"reflect"
	"testing"
)

// All traffic is to a disposable loopback registry fixture, never a real registry.
func TestLaunchpadMirroredTagsListUsesLegacyAllProtocol(t *testing.T) {
	requests := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Docker-Distribution-Api-Version", "registry/2.0")
		switch r.URL.Path {
		case "/v2/":
			w.WriteHeader(http.StatusOK)
		case "/v2/example/tags/list":
			requests++
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprint(w, `{"name":"example","tags":["z","a","m"]}`)
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()
	location, err := url.Parse(server.URL)
	if err != nil {
		t.Fatal(err)
	}
	ctx := context.Background()
	client := NewContext(server.Client().Transport, server.Client().Transport).WithCredentials(NoCredentials)
	repository, err := client.Repository(ctx, location, "example", true)
	if err != nil {
		t.Fatal(err)
	}
	page, err := repository.Tags(ctx).List(ctx, 1, "a")
	if err != nil || !reflect.DeepEqual(page, []string{"m"}) {
		t.Fatalf("page=%v error=%v", page, err)
	}
	if requests != 1 {
		t.Fatalf("expected one legacy tags request, got %d", requests)
	}
}
