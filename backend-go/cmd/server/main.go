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

const (
	// Public routes
	routeHealth  = "/health"
	routeRoot    = "/"
	routeDocs    = "/docs"
	routeSwagger = "/swagger-ui/*"

	// Public recipe routes
	routeRecipes            = "/recipes"
	routeRecipesID          = "/recipes/{id}"
	routeRecipesIngredients = "/recipes/{id}/ingredients"
	routeRecipesIngredient  = "/recipes/{id}/ingredients/{ingredient_id}"

	// Public USDA routes
	routeUsdaFood              = "/usda/food/{fdc_id}"
	routeUsdaFoods             = "/usda/foods"
	routeUsdaFoodsList         = "/usda/foods/list"
	routeUsdaSearch            = "/usda/search"
	routeUsdaSearchAdvanced    = "/usda/search/advanced"
	routeUsdaSearchIngredients = "/usda/search-ingredients"
	routeUsdaIngredient        = "/usda/ingredient/{fdc_id}"

	// Internal FastAPI paths
	internalRecipesPath = "/internal/recipes"
	internalUsdaPath    = "/internal/usda"

	// Server config
	serverReadTimeout     = 15 * time.Second
	serverWriteTimeout    = 15 * time.Second
	serverIdleTimeout     = 60 * time.Second
	serverShutdownTimeout = 30 * time.Second
	serverMaxHeaderBytes  = 1 << 20
)

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
	router.Get(routeHealth, healthHandler)
	router.Get(routeRoot, rootHandler)
	router.Get(routeDocs, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
		docs.SwaggerUIHandler(responseWriter, httpRequest)
	})
	router.Get(routeSwagger, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
		docs.SwaggerUIHandler(responseWriter, httpRequest)
	})

	// Protected routes group with auth and caching middleware
	router.Group(func(subRouter chi.Router) {
		subRouter.Use(middleware.AuthMiddleware(configuration))
		if configuration.CacheEnabled {
			subRouter.Use(middleware.CacheMiddleware(configuration, redisClient))
		}

		// BFF routes - map public endpoints to internal FastAPI endpoints
		subRouter.Get(routeRecipes, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalRecipesPath)
		})
		subRouter.Post(routeRecipes, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalRecipesPath)
		})
		subRouter.Get(routeRecipesID, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			id := chi.URLParam(httpRequest, "id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalRecipesPath+"/"+id)
		})
		subRouter.Put(routeRecipesID, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			id := chi.URLParam(httpRequest, "id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalRecipesPath+"/"+id)
		})
		subRouter.Delete(routeRecipesID, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			id := chi.URLParam(httpRequest, "id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalRecipesPath+"/"+id)
		})
		subRouter.Post(routeRecipesIngredients, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			id := chi.URLParam(httpRequest, "id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalRecipesPath+"/"+id+"/ingredients")
		})
		subRouter.Delete(routeRecipesIngredient, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			id := chi.URLParam(httpRequest, "id")
			ingredientID := chi.URLParam(httpRequest, "ingredient_id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalRecipesPath+"/"+id+"/ingredients/"+ingredientID)
		})

		// USDA endpoints
		subRouter.Get(routeUsdaFood, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			fdcID := chi.URLParam(httpRequest, "fdc_id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalUsdaPath+"/food/"+fdcID)
		})
		subRouter.Post(routeUsdaFoods, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalUsdaPath+"/foods")
		})
		subRouter.Post(routeUsdaFoodsList, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalUsdaPath+"/foods/list")
		})
		subRouter.Post(routeUsdaSearch, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalUsdaPath+"/search")
		})
		subRouter.Post(routeUsdaSearchAdvanced, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalUsdaPath+"/search/advanced")
		})
		subRouter.Get(routeUsdaSearchIngredients, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalUsdaPath+"/search-ingredients")
		})
		subRouter.Get(routeUsdaIngredient, func(responseWriter http.ResponseWriter, httpRequest *http.Request) {
			fdcID := chi.URLParam(httpRequest, "fdc_id")
			proxy.ProxyToInternal(reverseProxy, responseWriter, httpRequest, internalUsdaPath+"/ingredient/"+fdcID)
		})
	}) // End protected routes group

	// Create server
	server := &http.Server{
		Addr:           fmt.Sprintf(":%d", configuration.Port),
		Handler:        router,
		ReadTimeout:    serverReadTimeout,
		WriteTimeout:   serverWriteTimeout,
		IdleTimeout:    serverIdleTimeout,
		MaxHeaderBytes: serverMaxHeaderBytes,
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
	ctx, cancel := context.WithTimeout(context.Background(), serverShutdownTimeout)
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
