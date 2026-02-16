# EventFlow Makefile

.PHONY: help setup start stop restart logs test lint format clean

help:
	@echo "EventFlow - Distributed Event Processing System"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup      - Initial setup (install deps, create .env)"
	@echo "  make start      - Start all services"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make produce    - Send test events"
	@echo "  make monitor    - Monitor metrics"
	@echo "  make load-test  - Run load test"

setup:
	@echo "Setting up EventFlow..."
	pip install -r requirements.txt
	cp -n .env.example .env || true
	@echo "Setup complete!"

start:
	@echo "Starting services..."
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000"

stop:
	@echo "Stopping services..."
	docker-compose down

restart:
	@echo "Restarting services..."
	docker-compose restart

logs:
	docker-compose logs -f

test:
	@echo "Running tests..."
	pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration/ -v

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=common --cov=api --cov=worker --cov-report=html --cov-report=term

lint:
	@echo "Running linters..."
	flake8 .
	mypy common/ api/ worker/ --ignore-missing-imports

format:
	@echo "Formatting code..."
	black .

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage
	@echo "Cleanup complete!"

produce:
	@echo "Sending test events..."
	python scripts/producer.py --count 100 --rate 10

monitor:
	@echo "Monitoring metrics..."
	python scripts/monitor.py

load-test:
	@echo "Running load test..."
	python scripts/load_test.py --events 1000 --rate 100

scale-workers:
	@echo "Scaling workers to 5..."
	docker-compose up -d --scale worker=5

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | python -m json.tool

db-shell:
	@echo "Connecting to database..."
	docker-compose exec postgres psql -U eventflow -d eventflow

redis-shell:
	@echo "Connecting to Redis..."
	docker-compose exec redis redis-cli

install-dev:
	@echo "Installing development dependencies..."
	pip install pytest pytest-asyncio pytest-cov black flake8 mypy

ci:
	@echo "Running CI checks..."
	black --check .
	flake8 .
	mypy common/ api/ worker/ --ignore-missing-imports
	pytest --cov
	@echo "CI checks passed!"
