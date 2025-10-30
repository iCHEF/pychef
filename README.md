# pychef

Python utilities for iCHEF.

## Development

### Prerequisites
- uv
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
