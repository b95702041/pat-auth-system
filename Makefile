.PHONY: help build up down logs test shell migrate clean

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

.DEFAULT_GOAL := help
