.PHONY: help dev up down logs test clean install worker api redis-cli

# Default target
help:
	@echo "Resume Engine - Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install     Install Python dependencies"
	@echo "  make setup       First-time setup (install + download models)"
	@echo ""
	@echo "Local Development (Docker):"
	@echo "  make dev         Start all services (API + Worker + Redis)"
	@echo "  make up          Same as dev"
	@echo "  make down        Stop all services"
	@echo "  make logs        View logs from all services"
	@echo "  make logs-api    View API logs only"
	@echo "  make logs-worker View Worker logs only"
	@echo ""
	@echo "Individual Services:"
	@echo "  make api         Run API server locally (requires local Redis)"
	@echo "  make worker      Run ARQ worker locally (requires local Redis)"
	@echo "  make redis       Start Redis in Docker only"
	@echo ""
	@echo "Testing:"
	@echo "  make test        Run tests"
	@echo "  make test-redis  Test Redis connection"
	@echo ""
	@echo "Utilities:"
	@echo "  make redis-cli   Open Redis CLI"
	@echo "  make clean       Clean up containers and volumes"
	@echo "  make rebuild     Rebuild Docker images from scratch"
	@echo ""

# Installation
install:
	pip3 install -r requirements.txt

setup: install
	python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
	pip3 install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Docker Compose
dev: up

up:
	docker-compose up --build

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-worker:
	docker-compose logs -f worker

# Individual Services (Local)
api:
	@echo "Starting API server (make sure Redis is running)..."
	WORKER_MODE=false uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	@echo "Starting ARQ worker (make sure Redis is running)..."
	WORKER_MODE=true arq app.worker.WorkerSettings

redis:
	docker run -d --name resume-redis -p 6379:6379 redis:7-alpine

# Testing
test:
	pytest tests/ -v

test-redis:
	python3 test_redis_simple.py

# Utilities
redis-cli:
	docker-compose exec redis redis-cli

clean:
	docker-compose down -v
	docker system prune -f

rebuild:
	docker-compose build --no-cache
	docker-compose up

# Development Helpers
shell-api:
	docker-compose exec api /bin/bash

shell-worker:
	docker-compose exec worker /bin/bash

ps:
	docker-compose ps

restart:
	docker-compose restart

# Quick status check
status:
	@echo "Docker Services:"
	@docker-compose ps
	@echo ""
	@echo "Redis Connection:"
	@python3 test_redis_simple.py 2>/dev/null || echo "Redis not accessible locally (normal for Railway Redis)"
