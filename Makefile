PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
PYTEST ?= $(PYTHON) -m pytest

.DEFAULT_GOAL := help

.PHONY: help test test-fast test-fast-p test-all test-all-p test-slow test-lint \
	test-ebt test-arena test-mp test-linter test-services test-workflows test-reviewer test-meta test-lf

help: ## Zeigt alle verfügbaren Testprofile
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

test: test-fast ## Standard-Dev-Lauf (nur schnelle Tests, nutzt pyproject addopts)

test-fast: ## Schnelle Tests sequentiell (Dev-Default)
	$(PYTEST) -q

test-fast-p: ## Schnelle Tests parallel via pytest-xdist
	$(PYTEST) -n auto --dist loadscope -q

test-all: ## Komplette Suite inkl. slow + CI-Hypothesis-Profil
	$(PYTEST) -m "" --hypothesis-profile=ci -q

test-all-p: ## Komplette Suite parallel via pytest-xdist
	$(PYTEST) -n auto --dist loadscope -m "" --hypothesis-profile=ci -q

test-slow: ## Nur als slow markierte Tests
	$(PYTEST) -m slow -q

test-lint: ## Statische Analyse, Styleguide & Doku-Beispiele
	$(PYTEST) -m lint -q

test-ebt: ## Alle EBT-Core-Tests (inkl. slow)
	$(PYTEST) -m ebt -q

test-arena: ## Alle Arena-Tests (inkl. Resource-Limits)
	$(PYTEST) -m arena -q

test-mp: ## Alle Multiprocessing-Tests (inkl. Scaling & Hypothesis)
	$(PYTEST) -m multiprocess -q

test-linter: ## Alle Linter-Integrationstests
	$(PYTEST) -m linter -q

test-services: ## Alle Service-Tests (z. B. DocEnsurance)
	$(PYTEST) -m services -q

test-workflows: ## Alle User-Workflow-Tests
	$(PYTEST) -m workflows -q

test-reviewer: ## Alle RBT- & Reviewer-Tests
	$(PYTEST) -m reviewer -q

test-meta: ## Repo-Meta-Verträge, Offline- & Styleguide-Checks
	$(PYTEST) -m meta -q

test-lf: ## Zuletzt fehlgeschlagene Tests zuerst und bei Fehler stoppen
	$(PYTEST) --lf -x -q
