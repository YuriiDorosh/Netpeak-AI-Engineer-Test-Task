COMPOSE        := docker compose -f docker/docker-compose.yml
MODEL_DIR      := models
MODEL_FILENAME := qwen2.5-3b-instruct-q4_k_m.gguf
MODEL_URL      := https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf
BASE_URL       := http://localhost

.DEFAULT_GOAL := help

.PHONY: help download-model build up down logs ps process clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

download-model: ## Download Qwen2.5-3B GGUF (≈2 GB) to ./models/
	@mkdir -p $(MODEL_DIR)
	@if [ -f "$(MODEL_DIR)/$(MODEL_FILENAME)" ]; then \
		echo "✓ Model already present: $(MODEL_DIR)/$(MODEL_FILENAME)"; \
	else \
		echo "⬇  Downloading $(MODEL_FILENAME) ..."; \
		wget -c --show-progress -O "$(MODEL_DIR)/$(MODEL_FILENAME)" "$(MODEL_URL)"; \
		echo "✓ Done."; \
	fi

# ── Docker ─────────────────────────────────────────────────────────────────────

build: ## Build all Docker images
	$(COMPOSE) build

up: _check-model ## Start all services (detached)
	$(COMPOSE) up -d
	@echo ""
	@echo "  UI:      $(BASE_URL)/"
	@echo "  Swagger: $(BASE_URL)/docs"
	@echo ""
	@echo "(llm healthcheck may still be warming up — 'make logs' to watch)"

down: ## Stop and remove containers
	$(COMPOSE) down

logs: ## Follow logs from all services
	$(COMPOSE) logs -f

ps: ## Show service status
	$(COMPOSE) ps

# ── Usage ──────────────────────────────────────────────────────────────────────

process: ## Upload and process a CSV file  →  make process FILE=input_requests.csv
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make process FILE=<path-to.csv>"; exit 1; \
	fi
	@echo "Uploading $(FILE) ..."
	@JOB_ID=$$(curl -s -X POST "$(BASE_URL)/api/upload" \
		-F "file=@$(FILE)" \
		| python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])") && \
	echo "Job ID: $$JOB_ID" && \
	echo "" && \
	echo "Poll status:        curl $(BASE_URL)/api/jobs/$$JOB_ID" && \
	echo "Download output:    curl -O $(BASE_URL)/api/jobs/$$JOB_ID/output.json" && \
	echo "Download report:    curl -O $(BASE_URL)/api/jobs/$$JOB_ID/report.md"

# ── Dev ────────────────────────────────────────────────────────────────────────

clean: ## Remove stopped containers and dangling images
	$(COMPOSE) down --remove-orphans
	docker image prune -f

# ── Internal ───────────────────────────────────────────────────────────────────

_check-model:
	@if [ ! -f "$(MODEL_DIR)/$(MODEL_FILENAME)" ]; then \
		echo ""; \
		echo "Error: model not found at $(MODEL_DIR)/$(MODEL_FILENAME)"; \
		echo "Run:  make download-model"; \
		echo ""; \
		exit 1; \
	fi
