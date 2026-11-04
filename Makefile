PYTHON_VERSION := 3.11.18

build:
	python -m build

clear:
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage && rm -rf .pytest_cache
	rm -rf dist/

init-environment:
	uv venv .venv --python=$(PYTHON_VERSION)

upgrade-python:
	uv venv .venv --clear --python=$(PYTHON_VERSION)
	uv pip sync requirements/dev.compiled.txt

compile-dependencies:
	uv pip compile --no-strip-extras --python-version=$(PYTHON_VERSION) --output-file=requirements/dev.compiled.txt requirements/dev.txt

# Syncs into the active venv (or ./.venv) without checking its Python version.
# After bumping PYTHON_VERSION, run `make upgrade-python` instead.
sync-dependencies-dev:
	uv pip sync requirements/dev.compiled.txt

test:
	pytest --cov=src/pychef --cov-report=term-missing src/pychef
