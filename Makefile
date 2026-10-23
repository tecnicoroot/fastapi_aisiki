.DEFAULT_GOAL := help
DC := docker compose

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------- Docker
up: ## Sobe toda a stack (api, worker, postgres, redis, mailpit)
	$(DC) up -d --build

down: ## Derruba a stack
	$(DC) down

clean: ## Derruba a stack e apaga os volumes (dados!)
	$(DC) down -v

logs: ## Acompanha os logs (ex.: make logs s=worker)
	$(DC) logs -f $(s)

shell: ## Abre um shell no container da API
	$(DC) exec api bash

# ---------------------------------------------------------------- Banco
migrate: ## Aplica as migrations e o seed
	$(DC) run --rm prestart

migration: ## Cria nova migration (ex.: make migration m="add phone to users")
	$(DC) exec -u $$(id -u):$$(id -g) api alembic revision --autogenerate -m "$(m)"

downgrade: ## Reverte a última migration
	$(DC) exec api alembic downgrade -1

# ---------------------------------------------------------------- Qualidade
test: ## Roda os testes dentro do container
	$(DC) exec api pytest --cov

test-local: ## Roda os testes localmente (precisa do Postgres em localhost)
	uv run pytest --cov

lint: ## Ruff (lint + formatação)
	uv run ruff check .
	uv run ruff format --check .

format: ## Formata e corrige automaticamente
	uv run ruff format .
	uv run ruff check --fix .

typecheck: ## Mypy (strict)
	uv run mypy .

check: lint typecheck test-local ## Roda tudo (igual ao CI)

.PHONY: help up down clean logs shell migrate migration downgrade test test-local lint format typecheck check
