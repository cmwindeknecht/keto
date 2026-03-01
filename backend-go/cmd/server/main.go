package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"keto-api/internal/cache"
	"keto-api/internal/config"
	"keto-api/internal/docs"
	"keto-api/internal/middleware"
	"keto-api/internal/proxy"

	"github.com/go-chi/chi/v5"
)

const RECIPES_ROUTE = "/internal/recipes/"
const USDA_ROUTE = "/internal/usda/"

func main() {
	// Load configuration
	configuration := config.Load()

	if configuration.Debug {
		fmt.Printf("Starting Keto API Gateway\n")
		fmt.Printf("Port: %d\n", configuration.Port)
		fmt.Printf("FastAPI URL: %s\n", configuration.FastAPIURL)
		fmt.Printf("Cache Enabled: %v\n", configuration.CacheEnabled)
		fmt.Printf("Cache TTL: %v\n", configuration.CacheTTL)
	}

	// Initialize Redis client
	redisClient, redisClientInstantiationError := cache.NewRedisClient(configuration.RedisURL)
	if redisClientInstantiationError != nil {
		fmt.Printf("Warning: Failed to connect to Redis: %v\n", redisClientInstantiationError)
		fmt.Println("Continuing without caching...")
		configuration.CacheEnabled = false
	} else {
		defer redisClient.Close()
	}

	// Create reverse proxy
	reverseProxy, reverseProxyError := proxy.NewReverseProxy(configuration)
	if reverseProxyError != nil {
		fmt.Printf("Failed to create reverse proxy: %v\n", reverseProxyError)
		os.Exit(1)
	}

	// Setup router
	router := chi.NewRouter()

	// Add global middleware (must be before routes)
	router.Use(middleware.CORSMiddleware())
	router.Use(middleware.LoggingMiddleware())

	// Public endpoints (no auth required)
	router.Get("/health", healthHandler)
	router.Get("/", rootHandler)
	router.Get("/docs", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
		docs.SwaggerUIHandler(responseWriter, httpRequest)
	})
	router.Get("/swagger-ui/*", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
		docs.SwaggerUIHandler(responseWriter, httpRequest)
	})

	// Protected routes group with auth and caching middleware
	router.Group(func(subRouter chi.Router) {
		subRouter.Use(middleware.AuthMiddleware(configuration))
		if configuration.CacheEnabled {
			subRouter.Use(middleware.CacheMiddleware(configuration, redisClient))
		}

		// BFF routes - map public endpoints to internal FastAPI endpoints
		subRouter.Get("/recipes", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, RECIPES_ROUTE)
		})
		subRouter.Post("/recipes", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, RECIPES_ROUTE)
		})
		subRouter.Get("/recipes/{id}", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			id := chi.URLParam(httpRequest, "id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, RECIPES_ROUTE+id)
		})
		subRouter.Put("/recipes/{id}", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			id := chi.URLParam(httpRequest, "id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, RECIPES_ROUTE+id)
		})
		subRouter.Delete("/recipes/{id}", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			id := chi.URLParam(httpRequest, "id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, RECIPES_ROUTE+id)
		})
		subRouter.Post("/recipes/{id}/ingredients", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			id := chi.URLParam(httpRequest, "id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, RECIPES_ROUTE+id+"/ingredients")
		})
		subRouter.Delete("/recipes/{id}/ingredients/{ingredient_id}", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			id := chi.URLParam(httpRequest, "id")
			ingredientID := chi.URLParam(httpRequest, "ingredient_id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, RECIPES_ROUTE+id+"/ingredients/"+ingredientID)
		})

		// USDA endpoints
		subRouter.Get("/usda/food/{fdc_id}", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			fdcID := chi.URLParam(httpRequest, "fdc_id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, USDA_ROUTE+"food/"+fdcID)
		})
		subRouter.Post("/usda/foods", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, USDA_ROUTE+"foods")
		})
		subRouter.Post("/usda/foods/list", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, USDA_ROUTE+"foods/list")
		})
		subRouter.Post("/usda/search", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, USDA_ROUTE+"search")
		})
		subRouter.Post("/usda/search/advanced", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, USDA_ROUTE+"search/advanced")
		})
		subRouter.Get("/usda/search-ingredients", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, USDA_ROUTE+"search-ingredients")
		})
		subRouter.Get("/usda/ingredient/{fdc_id}", func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			fdcID := chi.URLParam(httpRequest, "fdc_id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, USDA_ROUTE+"ingredient/"+fdcID)
		})
	}) // End protected routes group

	// Create server
	server := &http.Server{
		Addr:           fmt.Sprintf(":%d", configuration.Port),
		Handler:        router,
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
		serverError := server.ListenAndServe()
		if serverError != nil && serverError != http.ErrServerClosed {
			fmt.Printf("Server error: %v\n", serverError)
			os.Exit(1)
		}
	}()

	// Wait for shutdown signal
	<-stop

	fmt.Println("\nShutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	serverShutdownError := server.Shutdown(ctx)
	if serverShutdownError != nil {
		fmt.Printf("Shutdown error: %v\n", serverShutdownError)
		os.Exit(1)
	}

	fmt.Println("Server stopped gracefully")
}

func healthHandler(responseWriter http.ResponseWriter, httpRequest *http.Request) {
	responseWriter.Header().Set("Content-Type", "application/json")
	responseWriter.Header().Set("X-Proxy-By", "keto-api-gateway")
	responseWriter.WriteHeader(http.StatusOK)
	fmt.Fprintf(responseWriter, `{"status":"ok","service":"keto-api-gateway"}`)
}

func rootHandler(responseWriter http.ResponseWriter, httpRequest *http.Request) {
	responseWriter.Header().Set("Content-Type", "application/json")
	responseWriter.Header().Set("X-Proxy-By", "keto-api-gateway")
	responseWriter.WriteHeader(http.StatusOK)
	fmt.Fprintf(responseWriter, `{"service":"Keto API Gateway","version":"0.1.0","docs":"http://localhost:8080/docs"}`)
}
