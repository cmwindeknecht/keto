package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"keto-api/internal/cache"
	"keto-api/internal/config"
	"keto-api/internal/docs"
	"keto-api/internal/middleware"
	"keto-api/internal/proxy"
)

func main() {
	// Load configuration
	cfg := config.Load()

	if cfg.Debug {
		fmt.Printf("Starting Keto API Gateway\n")
		fmt.Printf("Port: %d\n", cfg.Port)
		fmt.Printf("FastAPI URL: %s\n", cfg.FastAPIURL)
		fmt.Printf("Cache Enabled: %v\n", cfg.CacheEnabled)
		fmt.Printf("Cache TTL: %v\n", cfg.CacheTTL)
	}

	// Initialize Redis client
	rc, err := cache.NewRedisClient(cfg.RedisURL)
	if err != nil {
		fmt.Printf("Warning: Failed to connect to Redis: %v\n", err)
		fmt.Println("Continuing without caching...")
		cfg.CacheEnabled = false
	} else {
		defer rc.Close()
	}

	// Create reverse proxy
	reverseProxy, err := proxy.NewReverseProxy(cfg)
	if err != nil {
		fmt.Printf("Failed to create reverse proxy: %v\n", err)
		os.Exit(1)
	}

	// Setup router
	r := chi.NewRouter()

	// Add global middleware (must be before routes)
	r.Use(middleware.LoggingMiddleware())

	// Public endpoints (no auth required)
	r.Get("/health", healthHandler)
	r.Get("/", rootHandler)
	r.Get("/docs", func(w http.ResponseWriter, r *http.Request) {
		docs.SwaggerUIHandler(w, r)
	})
	r.Get("/swagger-ui/*", func(w http.ResponseWriter, r *http.Request) {
		docs.SwaggerUIHandler(w, r)
	})

	// Protected routes group with auth and caching middleware
	r.Group(func(r chi.Router) {
		r.Use(middleware.AuthMiddleware(cfg))
		if cfg.CacheEnabled {
			r.Use(middleware.CacheMiddleware(cfg, rc))
		}

	// BFF routes - map public endpoints to internal FastAPI endpoints
	r.Get("/recipes", func(w http.ResponseWriter, r *http.Request) {
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/recipes")
	})
	r.Post("/recipes", func(w http.ResponseWriter, r *http.Request) {
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/recipes")
	})
	r.Get("/recipes/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/recipes/"+id)
	})
	r.Put("/recipes/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/recipes/"+id)
	})
	r.Delete("/recipes/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/recipes/"+id)
	})
	r.Post("/recipes/{id}/ingredients", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/recipes/"+id+"/ingredients")
	})
	r.Delete("/recipes/{id}/ingredients/{ingredient_id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		ingredientID := chi.URLParam(r, "ingredient_id")
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/recipes/"+id+"/ingredients/"+ingredientID)
	})
	r.Post("/search-ingredients", func(w http.ResponseWriter, r *http.Request) {
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/recipes/search-ingredients")
	})

	// USDA endpoints
	r.Get("/usda/food/{fdc_id}", func(w http.ResponseWriter, r *http.Request) {
		fdcID := chi.URLParam(r, "fdc_id")
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/usda/food/"+fdcID)
	})
	r.Post("/usda/foods", func(w http.ResponseWriter, r *http.Request) {
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/usda/foods")
	})
	r.Post("/usda/foods/list", func(w http.ResponseWriter, r *http.Request) {
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/usda/foods/list")
	})
	r.Post("/usda/search", func(w http.ResponseWriter, r *http.Request) {
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/usda/search")
	})
	r.Post("/usda/search/advanced", func(w http.ResponseWriter, r *http.Request) {
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/usda/search/advanced")
	})
	r.Get("/usda/search-ingredients", func(w http.ResponseWriter, r *http.Request) {
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/usda/search-ingredients")
	})
	r.Get("/usda/ingredient/{fdc_id}", func(w http.ResponseWriter, r *http.Request) {
		fdcID := chi.URLParam(r, "fdc_id")
		proxy.ProxyToInternal(reverseProxy, w, r, "/internal/usda/ingredient/"+fdcID)
	})
	}) // End protected routes group

	// Create server
	server := &http.Server{
		Addr:           fmt.Sprintf(":%d", cfg.Port),
		Handler:        r,
		ReadTimeout:    15 * time.Second,
		WriteTimeout:   15 * time.Second,
		IdleTimeout:    60 * time.Second,
		MaxHeaderBytes: 1 << 20, // 1 MB
	}

	// Graceful shutdown channel
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)

	// Start server in goroutine
	go func() {
		fmt.Printf("Starting server on %s\n", server.Addr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Printf("Server error: %v\n", err)
			os.Exit(1)
		}
	}()

	// Wait for shutdown signal
	<-stop

	fmt.Println("\nShutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		fmt.Printf("Shutdown error: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Server stopped gracefully")
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Proxy-By", "keto-api-gateway")
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"status":"ok","service":"keto-api-gateway"}`)
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Proxy-By", "keto-api-gateway")
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"service":"Keto API Gateway","version":"0.1.0","docs":"http://localhost:8080/docs"}`)
}
