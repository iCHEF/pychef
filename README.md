# pychef

Python utilities for iCHEF.

## Development

### Prerequisites
- uv >= 0.13.6（0.13.6 起才下載得到 CPython 3.11.18，且含 eMudhra 憑證拒絕清單；`uv self update` 或 `pip install -U uv==0.13.6`）
- AWS CLI

### Setup
```bash
# Create the development environment (installs Python, dependencies, etc.)
make init-environment
source .venv/bin/activate
make sync-dependencies-dev
```

### Upgrading Python
Bump `PYTHON_VERSION` in the `Makefile`, then rebuild `.venv` with it:
```bash
make upgrade-python
pre-commit clean  # rebuild pre-commit hook environments on the new Python
```

### Available Commands
```bash
# Build package locally
make build
# Update package dependencies
make compile-dependencies
# Cleanup test & build caches
```

### Testing
```bash
make test
```
