# pychef

Python utilities for iCHEF.

## Development

### Prerequisites
- uv >= 0.13.6（0.13.6 起才下載得到 CPython 3.11.18，其 `ssl` 模組內建 eMudhra 憑證拒絕清單；`uv self update` 或 `pip install -U 'uv>=0.13.6'`）
- AWS CLI

### Setup
```bash
# Create the development environment (installs Python, dependencies, etc.)
make init-environment
source .venv/bin/activate
make sync-dependencies-dev
```

### Upgrading Python
When `PYTHON_VERSION` in the `Makefile` changes (bumped by you or pulled from upstream), rebuild `.venv`:
```bash
make upgrade-python
.venv/bin/pre-commit clean    # rebuild pre-commit hook environments on the new Python
.venv/bin/pre-commit install  # the git hook runs the pre-commit (and virtualenv) it was installed from
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
