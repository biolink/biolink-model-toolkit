.DEFAULT_GOAL := all
SHELL := bash
RUN := uv run

.PHONY: all
all: install test

.PHONY: install
install:
	uv sync

.PHONY: test
test:
	$(RUN) pytest tests

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -rf .pytest_cache
	rm -rf output test-output
	rm -rf dist
	rm -rf build

.PHONY: lint
lint:  ## Lint the codebase
	$(RUN) ruff check --diff --exit-zero src/ tests/ examples/
	$(RUN) ruff format --check --diff src/ tests/ examples/

.PHONY: format
format:  ## Format the codebase
	$(RUN) ruff check --fix --exit-zero src/ tests/ examples/
	$(RUN) ruff format src/ tests/ examples/