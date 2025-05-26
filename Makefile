SHELL := bash

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
VENV ?= .venv

ifeq ($(OS),Windows_NT)
    VENV_BIN := $(VENV)\\Scripts
else
    VENV_BIN := $(VENV)/bin
endif
VENV_PY := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

GREEN := \033[0;32m
YELLOW := \033[0;33m
RESET := \033[0m

.DEFAULT_GOAL := help

# Utility message functions
define echo_green
	@printf "$(GREEN)%s\n$(RESET)" "$1"
endef

define echo_yellow
	@printf "$(YELLOW)%s\n$(RESET)" "$1"
endef

ifdef VIRTUAL_ENV
    ACTIVE_PY := $(VIRTUAL_ENV)/bin/python
    ACTIVE_PIP := $(VIRTUAL_ENV)/bin/pip
else
    ifeq (,$(wildcard $(VENV_PY)))
        ACTIVE_PY := $(PYTHON)
        ACTIVE_PIP := $(PIP)
    else
        ACTIVE_PY := $(VENV_PY)
        ACTIVE_PIP := $(VENV_PIP)
    endif
endif

.PHONY: help
help:
	@echo "Available targets:" && \
	grep -E '^[a-zA-Z_-]+:.*?#' $(MAKEFILE_LIST) | \
	awk -F':.*?#' '{printf("  %-20s %s\n", $$1, $$2)}'

.PHONY: venv
venv:  # Create local virtual environment
	@echo "Creating virtual environment in $(VENV)" && \
	$(PYTHON) -m venv $(VENV)
	@$(VENV_PIP) install -U pip >/dev/null
	@$(call echo_green,"Virtual environment ready. Activate with 'source $(VENV_BIN)/activate'")

.PHONY: install-deps
install-deps:  # Install runtime dependencies
	@$(ACTIVE_PIP) install -r requirements.txt

.PHONY: install
install: install-deps  # Install package in editable mode
	@$(ACTIVE_PIP) install -e .

.PHONY: test test-verbose test-coverage test-module test-integration test-examples server-test

test:  # Run all unit tests
	@$(ACTIVE_PY) -m unittest discover $(ARGS)


test-verbose:  # Run tests with verbose output
	@$(ACTIVE_PY) -m unittest discover -v $(ARGS)


test-coverage:  # Run tests with coverage
	@command -v coverage >/dev/null || $(ACTIVE_PIP) install coverage >/dev/null
	@$(VENV_BIN)/coverage run -m unittest discover $(ARGS)
	@$(VENV_BIN)/coverage report


test-module:  # Run tests for a specific module, e.g. MODULE=tests.test_api
ifndef MODULE
	$(call echo_yellow,"Specify MODULE=<module path>") && exit 1
else
	@$(ACTIVE_PY) -m unittest $(MODULE) $(ARGS)
endif


test-integration:  # Run integration tests
	@$(ACTIVE_PY) -m unittest discover -s tests/integration -v $(ARGS)


test-examples:  # Run example programs to ensure they work
	@$(ACTIVE_PY) - <<-'PY'
	import io, contextlib, sys
	import uor_cli
	
	cases = [
	    ('examples/countdown.asm', '321'),
	    ('examples/block_demo.asm', 'HI'),
	]
	for path, expected in cases:
	    buf = io.StringIO()
	    with contextlib.redirect_stdout(buf):
	        uor_cli.main(['run', path])
	    out = buf.getvalue().strip()
	    if out != expected:
	        sys.exit(f"Example {path} produced '{out}', expected '{expected}'")
	print('Examples OK')
	PY

server-test:  # Run server related tests
	@$(ACTIVE_PY) -m unittest tests/test_api_server.py tests/test_async_server.py $(ARGS)

.PHONY: lint format type-check precommit

lint:  # Run code linters
	@command -v flake8 >/dev/null || $(ACTIVE_PIP) install flake8 >/dev/null
	@command -v pylint >/dev/null || $(ACTIVE_PIP) install pylint >/dev/null
	@$(VENV_BIN)/flake8 uor *.py tests examples >/dev/null && \
$(VENV_BIN)/pylint uor *.py tests examples >/dev/null
	@$(call echo_green,"Lint OK")

format:  # Format code using black
	@command -v black >/dev/null || $(ACTIVE_PIP) install black >/dev/null
	@$(VENV_BIN)/black uor *.py tests examples


type-check:  # Run mypy type checks
	@command -v mypy >/dev/null || $(ACTIVE_PIP) install mypy >/dev/null
	@$(VENV_BIN)/mypy uor

precommit: lint type-check test  # Run all pre-commit checks

.PHONY: build clean clean-all

build:  # Build package distribution
	@command -v build >/dev/null || $(ACTIVE_PIP) install build >/dev/null
	@$(ACTIVE_PY) -m build

clean:  # Remove build artifacts
	@rm -rf build dist *.egg-info */__pycache__ __pycache__

clean-all: clean  # Remove venv and coverage data
	@rm -rf $(VENV) .coverage htmlcov

.PHONY: ipfs-check server

ipfs-check:  # Verify IPFS daemon is reachable
	@$(ACTIVE_PY) - <<-'PY'
	import sys
	try:
	    import ipfshttpclient
	except Exception:
	    sys.exit("ipfshttpclient not installed")
	try:
	    with ipfshttpclient.connect() as c:
	        c.id()
	    print("IPFS daemon running")
	except Exception:
	    sys.exit("IPFS daemon not running")
	PY

server:  # Start Flask development server
	@$(ACTIVE_PY) server.py

.PHONY: example-countdown example-block

example-countdown:
	@$(ACTIVE_PY) uor_cli.py run examples/countdown.asm

example-block:
	@$(ACTIVE_PY) uor_cli.py run examples/block_demo.asm

