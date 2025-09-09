# Testing Setup

## Quick Setup

1. Install test dependencies:
```bash
pip install pytest pytest-django pytest-asyncio
```

2. Run tests:
```bash
pytest
```

## Test Files

- `test_models.py` - Tests database models
- `test_views.py` - Tests web pages and forms  
- `test_ai_service.py` - Tests AI integration

## Running Specific Tests

```bash
# Run all tests
pytest

# Run one file
pytest estimate/tests/test_models.py

# Run one test
pytest estimate/tests/test_models.py::TestPropertyInquiry::test_create_property_inquiry

# Verbose output
pytest -v
```

## Tests the following

### Models (`test_models.py`)
- Creating property inquiries
- Questionnaire progress tracking
- Estimate calculations
- Chart data formatting

### Views (`test_views.py`)
- Form submission
- Questionnaire flow
- Results display

### AI Service (`test_ai_service.py`)
- Mock AI responses
- Request validation
- Fallback behavior

## Configuration Files

### `pytest.ini`
```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = property_tool.settings
python_files = test_*.py
testpaths = estimate/tests
```

### `conftest.py`
Contains test fixtures (reusable test data):
- `client` - Django test client
- `sample_inquiry` - Basic property inquiry
- `completed_inquiry` - Finished questionnaire
- `sample_estimate` - Complete estimate

## Common Commands

```bash
# Basic test run
pytest

# With coverage
pytest --cov=estimate

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

