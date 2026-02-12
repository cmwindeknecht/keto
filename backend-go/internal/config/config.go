package config

import (
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/joho/godotenv"
)

type Config struct {
	Port            int
	FastAPIURL      string
	RedisURL        string
	JWTSecret       string
	APIKeys         []string
	CacheTTL        time.Duration
	CacheEnabled    bool
	Debug           bool
	RequestTimeout  time.Duration
}

func Load() *Config {
	// Load .env file if it exists (for local development)
	_ = godotenv.Load()

	return &Config{
		Port:           getEnvInt("PORT", 8080),
		FastAPIURL:     getEnv("FASTAPI_URL", "http://localhost:8000"),
		RedisURL:       getEnv("REDIS_URL", "redis:6379"),
		JWTSecret:      getEnv("JWT_SECRET", "your-secret-key-change-in-production"),
		APIKeys:        parseAPIKeys(getEnv("API_KEYS", "test-key,dev-key")),
		CacheTTL:       time.Duration(getEnvInt("CACHE_TTL", 300)) * time.Second,
		CacheEnabled:   getEnvBool("CACHE_ENABLED", true),
		Debug:          getEnvBool("DEBUG", false),
		RequestTimeout: time.Duration(getEnvInt("REQUEST_TIMEOUT", 30)) * time.Second,
	}
}

func getEnv(key string, defaultVal string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultVal
}

func getEnvInt(key string, defaultVal int) int {
	val := getEnv(key, "")
	if val == "" {
		return defaultVal
	}
	if intVal, err := strconv.Atoi(val); err == nil {
		return intVal
	}
	return defaultVal
}

func getEnvBool(key string, defaultVal bool) bool {
	val := strings.ToLower(getEnv(key, ""))
	if val == "" {
		return defaultVal
	}
	return val == "true" || val == "1" || val == "yes"
}

func parseAPIKeys(keysStr string) []string {
	var keys []string
	for _, key := range strings.Split(keysStr, ",") {
		key = strings.TrimSpace(key)
		if key != "" {
			keys = append(keys, key)
		}
	}
	return keys
}
