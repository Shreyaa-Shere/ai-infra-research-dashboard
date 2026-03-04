.PHONY: dev down logs lint format test migrate makemigrations seed

COMPOSE = docker compose -f infra/docker-compose.yml

dev:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

lint:
	$(COMPOSE) exec api ruff check src tests
	$(COMPOSE) exec web npm run lint

format:
	$(COMPOSE) exec api ruff format src tests
	$(COMPOSE) exec web npm run format

test:
	$(COMPOSE) exec api pytest
	$(COMPOSE) exec web npm run test

migrate:
	$(COMPOSE) exec api alembic upgrade head

makemigrations:
	$(COMPOSE) exec api alembic revision --autogenerate -m "$(MSG)"

seed:
	$(COMPOSE) exec api python scripts/seed.py
