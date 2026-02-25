package middleware

import (
	"bytes"
	"context"
	"crypto/md5"
	"fmt"
	"net/http"
	"strings"
	"time"

	"keto-api/internal/cache"
	"keto-api/internal/config"
)

type cachedResponseWriter struct {
	http.ResponseWriter
	statusCode int
	body       *bytes.Buffer
}

func (w *cachedResponseWriter) WriteHeader(statusCode int) {
	w.statusCode = statusCode
	w.ResponseWriter.WriteHeader(statusCode)
}

func (w *cachedResponseWriter) Write(b []byte) (int, error) {
	w.body.Write(b)
	return w.ResponseWriter.Write(b)
}

func CacheMiddleware(cfg *config.Config, rc *cache.RedisClient) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Only cache GET requests; invalidate on mutations
			if !cfg.CacheEnabled || r.Method != "GET" {
				if cfg.CacheEnabled && r.Method != "GET" {
					invalidateRelatedCaches(rc, r)
					next.ServeHTTP(w, r)
					return
				}
				next.ServeHTTP(w, r)
				return
			}

			// Only cache explicitly allowlisted paths
			fmt.Printf("[CACHE] checking if should cache path %s\n", r.URL.Path)
			if !shouldCachePath(r.URL.Path) {
				fmt.Printf("[CACHE] skipped caching path %s\n", r.URL.Path)
				next.ServeHTTP(w, r)
				return
			}

			cacheKey := generateCacheKey(r)

			// Try to get from cache
			ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
			cachedBody, err := rc.Get(ctx, cacheKey)
			cancel()

			if err == nil && cachedBody != nil {
				w.Header().Set("X-Cache", "HIT")
				w.Header().Set("Content-Type", "application/json")
				w.Header().Set("X-Proxy-By", "keto-api-gateway")
				w.WriteHeader(http.StatusOK)
				w.Write(cachedBody)
				return
			}

			// Cache miss - proceed with request
			wrapped := &cachedResponseWriter{
				ResponseWriter: w,
				statusCode:     http.StatusOK,
				body:           &bytes.Buffer{},
			}

			next.ServeHTTP(wrapped, r)

			// Cache successful responses
			if wrapped.statusCode == http.StatusOK {
				wrapped.ResponseWriter.Header().Set("X-Cache", "MISS")
				wrapped.ResponseWriter.Header().Set("X-Proxy-By", "keto-api-gateway")

				ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
				rc.Set(ctx, cacheKey, wrapped.body.Bytes(), cfg.CacheTTL)
				cancel()
				fmt.Printf("[CACHE] cached path %s\n", r.URL.Path)
			}
		})
	}
}

func generateCacheKey(r *http.Request) string {
	// Generate key: cache:{method}:{path}:{query_string}
	keyStr := fmt.Sprintf("cache:%s:%s:%s", r.Method, r.URL.Path, r.URL.RawQuery)
	hash := md5.Sum([]byte(keyStr))
	return fmt.Sprintf("cache:%x", hash)
}

func invalidateRelatedCaches(rc *cache.RedisClient, r *http.Request) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	path := r.URL.Path

	// Invalidate the exact path as GET
	rc.Delete(ctx, generateCacheKeyForPath("GET", path, ""))

	// Invalidate the parent path (e.g., /recipes/123/ingredients → /recipes/123 and /recipes)
	parts := strings.Split(strings.Trim(path, "/"), "/")
	for i := len(parts) - 1; i > 0; i-- {
		parentPath := "/" + strings.Join(parts[:i], "/")
		rc.Delete(ctx, generateCacheKeyForPath("GET", parentPath, ""))
	}
}

func generateCacheKeyForPath(method, path, query string) string {
	keyStr := fmt.Sprintf("cache:%s:%s:%s", method, path, query)
	hash := md5.Sum([]byte(keyStr))
	return fmt.Sprintf("cache:%x", hash)
}

// shouldCachePath returns true only for paths that should be cached.
// Add entries to cachePaths below to allowlist additional routes.
//
// Currently uses exact matching only.
// To also match sub-paths (e.g. "/usda/123456" when "/usda" is listed),
// uncomment the prefix-match block below.
func shouldCachePath(path string) bool {
	cachePaths := map[string]bool{
		"/usda":               true,
		"/search-ingredients": true,
	}
	// Exact match
	if cachePaths[path] {
		return true
	}
	// Prefix match — uncomment to also cache sub-paths (e.g. /usda/123456)
	// for p := range cachePaths {
	// 	if strings.HasPrefix(path, p+"/") {
	// 		return true
	// 	}
	// }
	return false
}
