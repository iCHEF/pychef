# pychef

Python utilities for iCHEF.

## Development

### Prerequisites
- uv >= 0.13.4（憑證清單安全更新的門檻；`uv self update` 或 `pip install -U uv==0.13.6`）
- AWS CLI

### Setup
```bash
# Create the development environment (installs Python, dependencies, etc.)
make init-environment
source .venv/bin/activate
make sync-dependencies-dev
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
