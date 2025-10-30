build:
	python -m build

clear:
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage && rm -rf .pytest_cache
	rm -rf dist/

init-environment:
	uv venv .venv --python=3.11.9

compile-dependencies:
	uv pip compile --no-strip-extras --output-file=requirements/dev.compiled.txt requirements/dev.txt

sync-dependencies-dev:
	uv pip sync requirements/dev.compiled.txt

test:
	pytest --cov=src/pychef --cov-report=term-missing src/pychef
