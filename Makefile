.PHONY: build up down restart logs test test-backend clean shell-backend db-reset detect-readers dev-backend dev-macos help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker containers
	docker compose build

up: ## Start all services in background
	docker compose up -d

down: ## Stop all services
	docker compose down

restart: down up ## Restart all services

logs: ## Tail service logs
	docker compose logs -f

test: test-backend ## Run all tests

test-backend: ## Run backend tests (uses SQLite in-memory)
	docker compose run --rm --no-deps backend python -m pytest tests/ -v

clean: ## Stop services, remove volumes and images
	docker compose down -v --rmi local
	rm -rf frontend/node_modules frontend/dist

shell-backend: ## Open a shell in the backend container
	docker compose exec backend bash

db-reset: ## Reset the database (drop and recreate volumes)
	docker compose down -v
	docker compose up -d db
	@echo "Waiting for database..."
	@sleep 3
	docker compose up -d backend
	@echo "Database reset complete."

detect-readers: ## Detect NFC readers on the host (run BEFORE docker)
	@echo "Detecting NFC readers on this machine..."
	@cd backend && pip install -q pyscard 2>/dev/null; python detect_readers.py

# ── macOS development (NFC reader requires native backend) ────────

dev-macos: ## macOS: start db + frontend in Docker, backend runs natively
	docker compose -f docker-compose.yml -f docker-compose.macos.yml up -d
	@echo ""
	@echo "  DB + Frontend are running in Docker."
	@echo "  Now run 'make dev-backend' in a separate terminal to start the backend natively."
	@echo ""

dev-backend: ## macOS: run backend natively with NFC reader access
	@echo "Starting backend natively (with NFC reader access)..."
	cd backend && \
		DATABASE_URL=postgresql://pulseid:$${POSTGRES_PASSWORD:-pulseid_secret}@localhost:5432/pulseid \
		PULSEID_API_KEY=$${PULSEID_API_KEY:-change-me-in-production} \
		PULSEID_SECRET_KEY=$${PULSEID_SECRET_KEY:-change-me-in-production} \
		PULSEID_USERNAME=$${PULSEID_USERNAME:-admin} \
		PULSEID_PASSWORD=$${PULSEID_PASSWORD:-$$(grep PULSEID_PASSWORD ../.env 2>/dev/null | cut -d= -f2 || echo admin)} \
		PULSEID_READER_FILTER=$${PULSEID_READER_FILTER:-} \
		python3 wsgi.py
