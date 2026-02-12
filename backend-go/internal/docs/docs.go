package docs

import (
	"embed"
	"net/http"
	"strings"
)

//go:embed swagger-ui/*
var swaggerUIFS embed.FS

// SwaggerUIHandler serves the Swagger UI
func SwaggerUIHandler(w http.ResponseWriter, r *http.Request) {
	// Handle both /docs and /swagger-ui/* paths
	path := r.URL.Path

	// Strip prefix if it exists
	if strings.HasPrefix(path, "/swagger-ui/") {
		path = strings.TrimPrefix(path, "/swagger-ui/")
	} else if strings.HasPrefix(path, "/docs") {
		path = strings.TrimPrefix(path, "/docs")
		if path == "" || path == "/" {
			path = ""
		}
	}

	// Default to index.html for root paths
	if path == "" || path == "/" {
		path = "index.html"
	}

	data, err := swaggerUIFS.ReadFile("swagger-ui/" + path)
	if err != nil {
		w.WriteHeader(http.StatusNotFound)
		return
	}

	// Set content type based on file extension
	switch {
	case strings.HasSuffix(path, ".html"):
		w.Header().Set("Content-Type", "text/html")
	case strings.HasSuffix(path, ".js"):
		w.Header().Set("Content-Type", "application/javascript")
	case strings.HasSuffix(path, ".css"):
		w.Header().Set("Content-Type", "text/css")
	case strings.HasSuffix(path, ".json"):
		w.Header().Set("Content-Type", "application/json")
	}

	w.Write(data)
}
