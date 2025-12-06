.PHONY: help build up down logs test shell migrate clean cli-help cli-users cli-tokens cli-stats cli-cleanup

help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start services"
	@echo "  make down     - Stop services"
	@echo "  make logs     - View logs"
	@echo "  make test     - Run tests"
	@echo "  make shell    - Open shell in API container"
	@echo "  make migrate  - Run database migrations"
	@echo "  make clean    - Clean up (remove containers and volumes)"
	@echo ""
	@echo "CLI Management:"
	@echo "  make cli-help       - Show CLI help"
	@echo "  make cli-users      - List all users"
	@echo "  make cli-tokens     - List all active tokens"
	@echo "  make cli-tokens-all - List all tokens (including revoked)"
	@echo "  make cli-stats      - Show system statistics"
	@echo "  make cli-cleanup    - Clean up old tokens (dry run)"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started. API available at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f api

test:
	docker-compose exec api pytest tests/ -v

test-cov:
	docker-compose exec api pytest tests/ --cov=app --cov-report=html

shell:
	docker-compose exec api /bin/bash

migrate:
	docker-compose exec api alembic upgrade head

clean:
	docker-compose down -v
	@echo "All containers and volumes removed"

restart: down up

# CLI Commands
cli-help:
	docker-compose exec api python -m app.cli --help

cli-users:
	docker-compose exec api python -m app.cli users list

cli-tokens:
	docker-compose exec api python -m app.cli tokens list

cli-tokens-all:
	docker-compose exec api python -m app.cli tokens list --all

cli-stats:
	docker-compose exec api python -m app.cli stats

cli-cleanup:
	docker-compose exec api python -m app.cli tokens cleanup --dry-run

# Database shortcuts
db-shell:
	docker-compose exec db psql -U pat_user -d pat_db

redis-cli:
	docker-compose exec redis redis-cli

.DEFAULT_GOAL := help