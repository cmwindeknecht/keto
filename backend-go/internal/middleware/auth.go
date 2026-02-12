package middleware

import (
	"context"
	"fmt"
	"net/http"
	"strings"

	"github.com/golang-jwt/jwt/v5"
	"keto-api/internal/config"
)

type authKey string

const UserContextKey authKey = "user"

type Claims struct {
	Subject string `json:"sub"`
	jwt.RegisteredClaims
}

func AuthMiddleware(cfg *config.Config) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip auth for public endpoints
			if shouldSkipAuth(r.Method, r.URL.Path) {
				next.ServeHTTP(w, r)
				return
			}

			// Try API Key auth first
			apiKey := r.Header.Get("X-API-Key")
			if apiKey != "" {
				if isValidAPIKey(apiKey, cfg.APIKeys) {
					ctx := context.WithValue(r.Context(), UserContextKey, apiKey)
					next.ServeHTTP(w, r.WithContext(ctx))
					return
				}
				http.Error(w, `{"detail":"Invalid API key"}`, http.StatusUnauthorized)
				return
			}

			// Try JWT auth
			authHeader := r.Header.Get("Authorization")
			if authHeader != "" {
				token := extractBearerToken(authHeader)
				if token != "" {
					claims, err := validateJWT(token, cfg.JWTSecret)
					if err == nil {
						ctx := context.WithValue(r.Context(), UserContextKey, claims.Subject)
						next.ServeHTTP(w, r.WithContext(ctx))
						return
					}
				}
				http.Error(w, `{"detail":"Invalid token"}`, http.StatusUnauthorized)
				return
			}

			// No auth provided
			http.Error(w, `{"detail":"Missing authorization"}`, http.StatusUnauthorized)
		})
	}
}

func shouldSkipAuth(method, path string) bool {
	// Public endpoints that don't require auth
	publicPaths := map[string]bool{
		"/health": true,
		"/":       true,
	}
	return publicPaths[path]
}

func isValidAPIKey(key string, validKeys []string) bool {
	for _, validKey := range validKeys {
		if key == validKey {
			return true
		}
	}
	return false
}

func extractBearerToken(authHeader string) string {
	parts := strings.Split(authHeader, " ")
	if len(parts) != 2 || parts[0] != "Bearer" {
		return ""
	}
	return parts[1]
}

func validateJWT(tokenString, secret string) (*Claims, error) {
	claims := &Claims{}
	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(secret), nil
	})

	if err != nil || !token.Valid {
		return nil, fmt.Errorf("invalid token: %w", err)
	}

	return claims, nil
}

func GetUserFromContext(ctx context.Context) string {
	user, ok := ctx.Value(UserContextKey).(string)
	if !ok {
		return "unknown"
	}
	return user
}
