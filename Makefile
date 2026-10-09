.PHONY: clean clean-build clean-pyc clean-test coverage dist docs help install lint test test-all docker-local docker-release
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

IMAGE      ?= asset-docs-integration
TAG        ?= $(shell git rev-parse --abbrev-ref HEAD | tr '/' '-')
VERSION    ?= $(shell awk -F'"' '/^version/ { print $$2; exit }' pyproject.toml)
GIT_COMMIT := $(shell git rev-parse HEAD)
GIT_REF    := $(shell git rev-parse --abbrev-ref HEAD)
BUILD_DATE := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache
	rm -fr .ruff_cache
	rm -fr .mypy_cache

lint: ## check style with ruff
	uv run ruff check asset_docs_integration tests
	uv run ruff format --check asset_docs_integration tests

test: ## run tests quickly with the default Python
	uv run pytest

test-all: ## run tests on every Python version with tox
	uv run tox

coverage: ## check code coverage quickly with the default Python
	uv run pytest --cov=./ --cov-report html:cov_html -sv
	$(BROWSER) ./cov_html/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/asset_docs_integration.rst
	rm -f docs/modules.rst
	uv run sphinx-apidoc -o docs/ asset_docs_integration
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	uv run watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

dist: clean ## build source and wheel package
	uv build
	ls -l dist

install: ## install dependencies into a project-local .venv via uv
	uv sync --extra test --extra dev
docker-local: ## build Docker image into the local daemon (no SBOM/provenance)
	docker buildx build \
		--load \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg GIT_REF=$(GIT_REF) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg VERSION=$(VERSION) \
		-t $(IMAGE):$(TAG) -t $(IMAGE):latest .

docker-release: ## build and push Docker image with SBOM + provenance attestations
	docker buildx build \
		--sbom=true --provenance=true \
		--output type=image,name=registry.axiom/$(IMAGE):$(VERSION),push=true,registry.insecure=true \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg GIT_REF=$(GIT_REF) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg VERSION=$(VERSION) \
		.
