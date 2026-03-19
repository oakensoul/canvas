.PHONY: install lint format test audit build clean check-all

install:
	pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .
	mypy canvas

format:
	ruff check --fix .
	ruff format .

test:
	pytest

audit:
	pip-audit

build:
	python -m build
	twine check dist/*

clean:
	rm -rf dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

check-all: lint test audit
