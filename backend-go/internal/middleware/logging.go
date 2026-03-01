package middleware

import (
	"bytes"
	"fmt"
	"net/http"
	"time"
)

// LoggingMiddleware logs HTTP requests
func LoggingMiddleware() func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

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
