package cache

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

type RedisClient struct {
	client *redis.Client
}

func NewRedisClient(redisURL string) (*RedisClient, error) {
	redisOptions, parseURLError := redis.ParseURL("redis://" + redisURL)
	if parseURLError != nil {
		return nil, fmt.Errorf("invalid redis URL: %w", parseURLError)
	}

	client := redis.NewClient(redisOptions)

	// Test connectionContext
	// context --- timed operation that allows you to cancel, have timeouts, and pass metadata
	connectionContext, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	clientPingError := client.Ping(connectionContext).Err()
	if clientPingError != nil {
		return nil, fmt.Errorf("failed to connect to redis: %w", clientPingError)
	}

	return &RedisClient{client: client}, nil
}

func (redisClient *RedisClient) Get(redisContext context.Context, key string) ([]byte, error) {
	value, getError := redisClient.client.Get(redisContext, key).Result()
	if getError == redis.Nil {
		return nil, nil
	}
	if getError != nil {
		return nil, getError
	}
	return []byte(value), nil
}

func (redisClient *RedisClient) Set(redisContext context.Context, key string, value []byte, ttl time.Duration) error {
	return redisClient.client.Set(redisContext, key, value, ttl).Err()
}

func (redisClient *RedisClient) Delete(redisContext context.Context, key string) error {
	return redisClient.client.Del(redisContext, key).Err()
}

func (redisClient *RedisClient) HealthCheck(redisContext context.Context) error {
	return redisClient.client.Ping(redisContext).Err()
}

func (redisClient *RedisClient) Close() error {
	return redisClient.client.Close()
}
