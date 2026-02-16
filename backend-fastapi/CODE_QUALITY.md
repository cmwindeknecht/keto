# Code Quality & Linting Guide

This document describes how to use the code quality tools and SonarQube for the Keto backend.

## Tools Overview

| Tool | Purpose | Speed | Config |
|------|---------|-------|--------|
| **Black** | Code formatting | Fast | `pyproject.toml` |
| **isort** | Import sorting | Fast | `pyproject.toml` |
| **Pylint** | Code analysis | Slow | `.pylintrc` |
| **Flake8** | Style guide | Fast | `.flake8` |
| **MyPy** | Type checking | Medium | `pyproject.toml` |
| **Bandit** | Security | Fast | `.bandit` |
| **SonarQube** | Dashboard | N/A | `sonar-project.properties` |

## Quick Start

### Format your code
```bash
# Auto-fix formatting and imports
make format

# Or manually:
cd backend-fastapi
black app/ tests/
isort app/ tests/
```

### Run all checks
```bash
# Lint everything
make lint

# Type check
make type-check

# Security check
make security

# Run all tests with coverage
cd backend-fastapi
pytest --cov=app --cov-report=html
```

## Individual Tools

### Black (Code Formatting)
```bash
cd backend-fastapi

# Check formatting
black --check app/

# Fix formatting
black app/
```

**Config**: `pyproject.toml`
- Line length: 150
- Target: Python 3.11

### isort (Import Sorting)
```bash
cd backend-fastapi

# Check imports
isort --check-only app/

# Fix imports
isort app/
```

**Config**: `pyproject.toml`
- Profile: black
- Line length: 150

### Pylint (Code Analysis)
```bash
cd backend-fastapi

# Run pylint
pylint app/

# Generate report
pylint app/ --exit-zero -f json > pylint-report.json
```

**Config**: `.pylintrc`
- Max line length: 150
- Disabled: docstring requirements, too-few-public-methods

### Flake8 (PEP8 Style)
```bash
cd backend-fastapi

# Run flake8
flake8 app/

# Show statistics
flake8 app/ --statistics
```

**Config**: `.flake8`
- Max line length: 150
- Ignores: E203, W503, E501

### MyPy (Type Checking)
```bash
cd backend-fastapi

# Run type check
mypy app/

# Strict mode
mypy app/ --strict
```

**Config**: `pyproject.toml`
- Python 3.11
- Check untyped defs
- Optional type checking

### Bandit (Security)
```bash
cd backend-fastapi

# Run security check
bandit -r app/

# JSON output
bandit -r app/ -f json -o bandit-report.json
```

**Config**: `.bandit`
- Skips: B101 (assert_used in tests)

## SonarQube

### Start SonarQube
```bash
# Start all services including SonarQube
make up

# Check health
make sonarqube-status

# View logs
make sonarqube-logs
```

SonarQube runs on: **http://localhost:9000**

Default credentials:
- Username: `admin`
- Password: `admin` (change on first login)

### Initial Setup

1. **Login**: http://localhost:9000
2. **Create Project**: Click "Create project" → "Local"
3. **Project Key**: `keto-backend`
4. **Generate Token**: Administration → Security → Users → Generate token

### Run Analysis

#### Option 1: Using sonar-scanner (local)
```bash
# Install sonar-scanner globally
npm install -g sonarqube-scanner

# Or download from: https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/

# Run analysis
cd backend-fastapi
sonar-scanner \
  -Dsonar.projectKey=keto-backend \
  -Dsonar.sources=app \
  -Dsonar.tests=tests \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=YOUR_TOKEN_HERE
```

#### Option 2: Using Makefile (requires sonar-scanner)
```bash
make sonarqube-scan
```

This will:
- Run tests with coverage
- Generate pylint report
- Run SonarQube analysis

### Analyze Results

1. **Dashboard**: View overall code quality metrics
2. **Issues**: Browse by type, severity, assignee
3. **Hotspots**: Security-sensitive code needing review
4. **Coverage**: Test coverage by file/function
5. **Duplication**: Identify duplicated code
6. **Complexity**: Cyclomatic complexity analysis

### Integration with Git

#### GitHub Actions
CI/CD pipeline automatically:
- Runs linting
- Runs tests
- Generates coverage report
- (Optional: uploads to SonarQube Cloud)

See `.github/workflows/lint-and-test.yml`

## Fixing Common Issues

### Black Conflicts with Pylint
Black uses line length 150, pylint defaults to 80. Fixed in configs:
- `.pylintrc`: `max_line_length=150`
- `.flake8`: `max_line_length = 150`
- `pyproject.toml`: `line-length = 150`

### isort Conflicts with Black
Configured to use Black profile:
```toml
[tool.isort]
profile = "black"
```

### Type Hints Not Enforced
MyPy is configured permissively:
- `disallow_untyped_defs = false` (optional)
- `check_untyped_defs = true` (light checking)

For stricter checking, run: `mypy app/ --strict`

### Security Issues from Bandit
Some checks may be false positives. Suppress with:
```python
# bandit: disable=B101
```

## Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
cd backend-fastapi
black --check app/ tests/ || exit 1
flake8 app/ || exit 1
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Continuous Integration

Pipeline runs on every push/PR:
1. **Format Check** - Black
2. **Import Check** - isort
3. **Lint** - Pylint
4. **Style** - Flake8
5. **Types** - MyPy
6. **Security** - Bandit
7. **Tests** - pytest with coverage

## Best Practices

1. **Format Before Commit**: `make format` or `make lint-fix`
2. **Check Locally First**: Run `make lint` before pushing
3. **Fix Immediately**: Address issues as they appear
4. **Review SonarQube**: Check dashboard for trends
5. **Monitor Coverage**: Keep test coverage above 80%
6. **Security First**: Address Bandit findings immediately

## Configuration Files

- `.pylintrc` - Pylint configuration
- `.flake8` - Flake8 configuration
- `.bandit` - Bandit configuration
- `pyproject.toml` - Black, isort, mypy configuration
- `sonar-project.properties` - SonarQube configuration
- `.github/workflows/lint-and-test.yml` - CI/CD pipeline

## Useful Commands

```bash
# Format and lint in one go
make lint-fix

# Run tests with coverage report in browser
cd backend-fastapi
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Check code metrics
cd backend-fastapi
pylint app/ --disable=all --enable=metrics

# Find complexity hotspots
cd backend-fastapi
pylint app/ --disable=all --enable=R0912,R0913,R0914

# Generate full report
cd backend-fastapi
pylint app/ > pylint-full-report.txt
```

## Resources

- [SonarQube Docs](https://docs.sonarqube.org)
- [Black Docs](https://black.readthedocs.io)
- [isort Docs](https://pycqa.github.io/isort/)
- [Pylint Docs](https://pylint.pycqa.org)
- [MyPy Docs](https://mypy.readthedocs.io)
- [Bandit Docs](https://bandit.readthedocs.io)
