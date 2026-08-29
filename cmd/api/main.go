package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/Mohamad-Moghadam/portfolio-api/internal/config"
)

func main() {
    cfg, err := config.Load()
    if err != nil {
        log.Fatal(err)
    }

    mux := http.NewServeMux()

    mux.HandleFunc("GET /api/health", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        fmt.Fprint(w, `{"status":"ok"}`)
    })

    addr := fmt.Sprintf(":%d", cfg.Port)
    log.Printf("starting server (env=%s) on %s", cfg.Env, addr)
    log.Fatal(http.ListenAndServe(addr, mux))
}