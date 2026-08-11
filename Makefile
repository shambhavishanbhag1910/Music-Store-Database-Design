SHELL := /bin/bash

.PHONY: help env up down reset seed etl test lint logs ps

help:
	@echo "Music Store Data Platform"
	@echo "  make env    - create .env from .env.example"
	@echo "  make up     - start PostgreSQL OLTP, warehouse, Airflow and Grafana"
	@echo "  make seed   - generate deterministic synthetic OLTP data"
	@echo "  make etl    - run the ETL pipeline once"
	@echo "  make test   - run unit tests"
	@echo "  make lint   - run Ruff"
	@echo "  make reset  - destroy local volumes and rebuild from scratch"
	@echo "  make down   - stop services"
	@echo "  make ps     - show container status"

env:
	@test -f .env || cp .env.example .env
	@echo ".env is ready. Change default passwords before shared use."

up: env
	docker compose up -d --build

seed: env
	docker compose --profile tools run --rm pipeline python scripts/generate_demo_data.py --reset --customers 500 --artists 80 --albums 160 --tracks 1800 --orders 4000

etl: env
	docker compose --profile tools run --rm pipeline music-store-etl run

test:
	python -m pytest -q

lint:
	ruff check src tests scripts airflow/dags

logs:
	docker compose logs -f airflow grafana

ps:
	docker compose ps

down:
	docker compose down

reset:
	docker compose down -v --remove-orphans
	docker compose up -d --build
