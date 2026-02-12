package middleware

import (
	"bytes"
	"context"
	"crypto/md5"
	"fmt"
	"io"
	"net/http"
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
			// Only cache GET requests
			if !cfg.CacheEnabled || r.Method != "GET" {
				next.ServeHTTP(w, r)
				return
			}

			// Skip caching for certain paths
			if shouldSkipCaching(r.URL.Path) {
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

func shouldSkipCaching(path string) bool {
	skipPaths := map[string]bool{
		"/health": true,
		"/":       true,
	}
	return skipPaths[path]
}

// LoggingMiddleware logs HTTP requests
func LoggingMiddleware() func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			// Wrap response writer to capture status
			wrapped := &cachedResponseWriter{
				ResponseWriter: w,
				statusCode:     http.StatusOK,
				body:           &bytes.Buffer{},
			}

			next.ServeHTTP(wrapped, r)

			duration := time.Since(start)
			fmt.Printf("[%s] %s %s %d %v\n", time.Now().Format("2006-01-02 15:04:05"), r.Method, r.URL.Path, wrapped.statusCode, duration)
		})
	}
}

// ResponseWriterCapture wraps http.ResponseWriter to capture status and body
type ResponseWriterCapture struct {
	http.ResponseWriter
	statusCode int
	body       *bytes.Buffer
	headerSent bool
}

func (w *ResponseWriterCapture) WriteHeader(statusCode int) {
	if !w.headerSent {
		w.statusCode = statusCode
		w.headerSent = true
		w.ResponseWriter.WriteHeader(statusCode)
	}
}

func (w *ResponseWriterCapture) Write(b []byte) (int, error) {
	if !w.headerSent {
		w.WriteHeader(http.StatusOK)
	}
	w.body.Write(b)
	return w.ResponseWriter.Write(b)
}
