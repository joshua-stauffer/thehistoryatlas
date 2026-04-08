# The History Atlas — Makefile
# ============================================================

SHELL := /bin/bash

# Virtualenv
VENV := env
SERVER_DIR := server
CLIENT_DIR := client
TEXT_READER_DIR := text_reader

# Text reader defaults (override on the command line)
MODEL       ?= opus
SEC_MODEL   ?= sonnet
CLIENT_TYPE ?= code
FILE        ?=
TITLE       ?=
AUTHOR      ?=
PUBLISHER   ?= Unknown
PUB_DATE    ?=
START_PAGE  ?= 1
END_PAGE    ?=
PDF_OFFSET  ?= 0

# ---- Server ----------------------------------------------------------------

.PHONY: server
server: ## Start the FastAPI server (sources .env.local)
	cd $(SERVER_DIR) && source ../.env.local && \
		../$(VENV)/bin/uvicorn the_history_atlas.main:app --reload

# ---- Client ----------------------------------------------------------------

.PHONY: client
client: ## Start the React dev server
	cd $(CLIENT_DIR) && npm start

# ---- Tests -----------------------------------------------------------------

.PHONY: test-server
test-server: ## Run server tests (sources .test_env)
	cd $(SERVER_DIR) && source ../.test_env && \
		../$(VENV)/bin/pytest -vvv

.PHONY: test-client
test-client: ## Run client tests in CI mode
	cd $(CLIENT_DIR) && npm run test:ci

.PHONY: test-text-reader
test-text-reader: ## Run text_reader tests
	cd $(TEXT_READER_DIR) && ../$(VENV)/bin/pytest -vvv

.PHONY: test
test: test-server test-client test-text-reader ## Run all tests

# ---- Lint / Format ---------------------------------------------------------

.PHONY: lint-server
lint-server: ## Format server Python with black
	cd $(SERVER_DIR) && ../$(VENV)/bin/black .

.PHONY: lint-client
lint-client: ## Format client with prettier
	cd $(CLIENT_DIR) && npx prettier --write src/

.PHONY: lint-text-reader
lint-text-reader: ## Format text_reader Python with black
	cd $(TEXT_READER_DIR) && ../$(VENV)/bin/black .

.PHONY: lint
lint: lint-server lint-client lint-text-reader ## Format all code

# ---- Text Reader -----------------------------------------------------------

.PHONY: extract
extract: ## Run the text reader extraction pipeline
extract: ## Usage: make extract FILE=path.pdf TITLE="..." AUTHOR="..."
extract: ## Optional: MODEL, SEC_MODEL, START_PAGE, END_PAGE, PDF_OFFSET, PUBLISHER, PUB_DATE
	@if [ -z "$(FILE)" ] || [ -z "$(TITLE)" ] || [ -z "$(AUTHOR)" ]; then \
		echo "Usage: make extract FILE=path.pdf TITLE=\"...\" AUTHOR=\"...\""; \
		echo "Optional: MODEL=$(MODEL) SEC_MODEL=$(SEC_MODEL) START_PAGE= END_PAGE= PDF_OFFSET= PUBLISHER= PUB_DATE="; \
		exit 1; \
	fi
	cd $(TEXT_READER_DIR) && ../$(VENV)/bin/python main.py \
		--client $(CLIENT_TYPE) \
		--model $(MODEL) \
		--secondary-model $(SEC_MODEL) \
		--file "$(FILE)" \
		--title "$(TITLE)" \
		--author "$(AUTHOR)" \
		--publisher "$(PUBLISHER)" \
		$(if $(PUB_DATE),--pub-date "$(PUB_DATE)") \
		--start-page $(START_PAGE) \
		$(if $(END_PAGE),--end-page $(END_PAGE)) \
		--pdf-offset $(PDF_OFFSET)

.PHONY: resume
resume: ## Resume an interrupted extraction
resume: ## Usage: make resume STATE=logs/state_file.json
	@if [ -z "$(STATE)" ]; then \
		echo "Usage: make resume STATE=logs/state_file.json"; \
		exit 1; \
	fi
	cd $(TEXT_READER_DIR) && ../$(VENV)/bin/python main.py \
		--client $(CLIENT_TYPE) \
		--model $(MODEL) \
		--secondary-model $(SEC_MODEL) \
		--resume "$(STATE)"

# ---- Auth ------------------------------------------------------------------

SERVER_URL ?= https://api.historyatlas.org

.PHONY: token
token: ## Get an API token
token: ## Usage: make token USER=admin PASS=secret [SERVER_URL=https://...]
	@if [ -z "$(USER)" ] || [ -z "$(PASS)" ]; then \
		echo "Usage: make token USER=admin PASS=secret [SERVER_URL=$(SERVER_URL)]"; \
		exit 1; \
	fi
	@curl -s -X POST "$(SERVER_URL)/token" \
		-H "Content-Type: application/x-www-form-urlencoded" \
		-d "username=$(USER)&password=$(PASS)" | python3 -c \
		"import sys,json; d=json.load(sys.stdin); print(d.get('access_token') or d)"

KEY_NAME ?= text-reader

.PHONY: api-key
api-key: ## Create an API key (requires TOKEN from 'make token')
api-key: ## Usage: make api-key TOKEN=... [KEY_NAME=text-reader] [SERVER_URL=https://...]
	@if [ -z "$(TOKEN)" ]; then \
		echo "Usage: make api-key TOKEN=<jwt-from-make-token> [KEY_NAME=$(KEY_NAME)] [SERVER_URL=$(SERVER_URL)]"; \
		echo ""; \
		echo "Step 1: make token USER=admin PASS=secret"; \
		echo "Step 2: make api-key TOKEN=<output-from-step-1>"; \
		exit 1; \
	fi
	@curl -s -X POST "$(SERVER_URL)/api-keys" \
		-H "Authorization: Bearer $(TOKEN)" \
		-H "Content-Type: application/json" \
		-d '{"name":"$(KEY_NAME)"}' | python3 -c \
		"import sys,json; d=json.load(sys.stdin); k=d.get('raw_key'); print(f'THA_API_KEY={k}' if k else d)"

# ---- Help ------------------------------------------------------------------

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
