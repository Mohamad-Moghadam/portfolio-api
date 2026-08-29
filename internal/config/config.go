package config

import (
	"fmt"
	"os"
	"strconv"
)

type Config struct {
    Port int
    Env  string // "dev" or "prod"
}

func Load() (*Config, error) {
    port, err := getEnvInt("PORT", 8080)
    if err != nil {
        return nil, err
    }

    return &Config{
        Port: port,
        Env:  getEnvString("ENV", "dev"),
    }, nil
}

func getEnvString(key, fallback string) string {
    val, ok := os.LookupEnv(key)
    if !ok || val == "" {
        return fallback
    }
    return val
}

func getEnvInt(key string, fallback int) (int, error) {
    val, ok := os.LookupEnv(key)
    if !ok || val == "" {
        return fallback, nil
    }
    n, err := strconv.Atoi(val)
    if err != nil {
        return 0, fmt.Errorf("env var %s: %q is not a valid integer", key, val)
    }
    return n, nil
}