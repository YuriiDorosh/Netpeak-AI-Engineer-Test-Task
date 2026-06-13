# Extends the official llama.cpp server image with curl
# so docker compose healthcheck works out of the box.
FROM ghcr.io/ggerganov/llama.cpp:server

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
