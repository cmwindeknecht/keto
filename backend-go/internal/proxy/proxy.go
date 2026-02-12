package proxy

import (
	"fmt"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"time"

	"keto-api/internal/config"
	"keto-api/internal/middleware"
)

func NewReverseProxy(cfg *config.Config) (*httputil.ReverseProxy, error) {
	targetURL, err := url.Parse(cfg.FastAPIURL)
	if err != nil {
		return nil, fmt.Errorf("invalid FastAPI URL: %w", err)
	}

	proxy := httputil.NewSingleHostReverseProxy(targetURL)

	// Custom transport with timeout
	transport := &http.Transport{
		Dial: (&net.Dialer{
			Timeout:   10 * time.Second,
			KeepAlive: 60 * time.Second,
		}).Dial,
		TLSHandshakeTimeout: 10 * time.Second,
		IdleConnTimeout:     60 * time.Second,
		ResponseHeaderTimeout: cfg.RequestTimeout,
	}

	proxy.Transport = transport

	// Customize request before sending
	proxy.Director = func(req *http.Request) {
		req.URL.Scheme = targetURL.Scheme
		req.URL.Host = targetURL.Host
		req.RequestURI = ""

		// Add forwarding headers
		if clientIP := req.Header.Get("X-Forwarded-For"); clientIP == "" {
			req.Header.Set("X-Forwarded-For", getClientIP(req))
		}
		if proto := req.Header.Get("X-Forwarded-Proto"); proto == "" {
			req.Header.Set("X-Forwarded-Proto", "http")
		}

		// Don't forward auth headers to avoid credential leakage
		req.Header.Del("Authorization")
		req.Header.Del("X-API-Key")

		// Preserve user info from auth in custom header for logging
		if user := middleware.GetUserFromContext(req.Context()); user != "unknown" {
			req.Header.Set("X-User-ID", user)
		}
	}

	// Customize response
	originalModifyResponse := proxy.ModifyResponse
	proxy.ModifyResponse = func(resp *http.Response) error {
		if originalModifyResponse != nil {
			if err := originalModifyResponse(resp); err != nil {
				return err
			}
		}

		// Add proxy header
		resp.Header.Set("X-Proxy-By", "keto-api-gateway")

		// Ensure CORS headers
		if resp.Header.Get("Access-Control-Allow-Origin") == "" {
			resp.Header.Set("Access-Control-Allow-Origin", "*")
		}
		if resp.Header.Get("Access-Control-Allow-Methods") == "" {
			resp.Header.Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		}
		if resp.Header.Get("Access-Control-Allow-Headers") == "" {
			resp.Header.Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key")
		}

		return nil
	}

	// Handle errors
	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadGateway)
		fmt.Fprintf(w, `{"detail":"Error communicating with backend: %s"}`, err.Error())
	}

	return proxy, nil
}

func getClientIP(r *http.Request) string {
	// Try X-Forwarded-For first (for proxied requests)
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		return forwarded
	}

	// Try X-Real-IP
	if realIP := r.Header.Get("X-Real-IP"); realIP != "" {
		return realIP
	}

	// Fall back to remote address
	ip, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return ip
}
