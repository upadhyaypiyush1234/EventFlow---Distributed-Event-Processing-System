# Contributing to EventFlow

Thank you for your interest in contributing to EventFlow! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Docker version, etc.)
- Relevant logs or error messages

### Suggesting Features

Feature suggestions are welcome! Please create an issue with:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if you have ideas)
- Potential trade-offs or concerns

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Ensure tests pass:** `pytest`
6. **Update documentation** if needed
7. **Commit with clear messages:** `git commit -m "Add feature X"`
8. **Push to your fork:** `git push origin feature/your-feature-name`
9. **Create a pull request**

## Development Setup

### Prerequisites

- Docker Desktop
- Python 3.11+
- Git

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/eventflow.git
cd eventflow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Start services
docker-compose up -d

# Run tests
pytest
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use meaningful variable names
- Add docstrings to functions and classes

### Example

```python
async def process_event(event: Event, worker_id: str) -> bool:
    """
    Process a single event with validation and enrichment.
    
    Args:
        event: The event to process
        worker_id: Identifier of the processing worker
        
    Returns:
        bool: True if processing succeeded, False otherwise
    """
    # Implementation
```

### Formatting

Use `black` for code formatting:

```bash
pip install black
black .
```

### Linting

Use `flake8` for linting:

```bash
pip install flake8
flake8 .
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_models.py

# With coverage
pytest --cov=. --cov-report=html

# Verbose output
pytest -v
```

### Writing Tests

- Write tests for new features
- Test both happy paths and error cases
- Use descriptive test names
- Keep tests isolated and independent

### Example Test

```python
import pytest
from common.models import Event, EventType

def test_event_creation():
    """Test creating a valid event"""
    event = Event(
        event_type=EventType.PURCHASE,
        user_id="user123",
        properties={"amount": 99.99}
    )
    assert event.event_type == EventType.PURCHASE
    assert event.user_id == "user123"

def test_event_validation():
    """Test event validation fails for invalid data"""
    with pytest.raises(ValidationError):
        Event(event_type="invalid_type")
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Include parameter descriptions and return values
- Provide usage examples for complex functions

### README Updates

- Update README.md if you add new features
- Keep documentation in sync with code
- Add examples for new functionality

### Architecture Documentation

- Update ARCHITECTURE.md for significant changes
- Explain design decisions and trade-offs
- Include diagrams if helpful

## Commit Messages

### Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat: Add authentication to API endpoints

Implement JWT-based authentication for all API endpoints.
Users must provide a valid token in the Authorization header.

Closes #123
```

```
fix: Handle database connection timeout

Add retry logic for database connection failures.
Use exponential backoff with max 3 retries.

Fixes #456
```

## Project Structure

```
eventflow/
├── api/                    # FastAPI service
│   ├── main.py            # API endpoints
│   └── __init__.py
├── worker/                 # Event processors
│   ├── main.py            # Worker entry point
│   ├── processor.py       # Processing logic
│   └── __init__.py
├── common/                 # Shared utilities
│   ├── config.py          # Configuration
│   ├── database.py        # Database models
│   ├── models.py          # Pydantic models
│   ├── metrics.py         # Prometheus metrics
│   ├── logging_config.py  # Logging setup
│   ├── redis_client.py    # Redis client
│   └── __init__.py
├── tests/                  # Test suites
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── __init__.py
├── scripts/                # Utility scripts
│   ├── producer.py        # Event generator
│   ├── monitor.py         # Metrics monitor
│   └── load_test.py       # Load testing
├── config/                 # Configuration files
│   ├── prometheus.yml     # Prometheus config
│   └── grafana-datasources.yml
├── docker-compose.yml      # Service orchestration
├── Dockerfile.api          # API container
├── Dockerfile.worker       # Worker container
├── requirements.txt        # Python dependencies
└── README.md              # Project overview
```

## Adding New Features

### Example: Adding a New Event Type

1. **Update models:**
```python
# common/models.py
class EventType(str, Enum):
    PURCHASE = "purchase"
    USER_SIGNUP = "user_signup"
    PAGE_VIEW = "page_view"
    NEW_TYPE = "new_type"  # Add new type
```

2. **Add validation:**
```python
# worker/processor.py
async def _validate_event(self, event: Event):
    if event.event_type == "new_type":
        # Add validation logic
        if not event.properties.get("required_field"):
            raise ValueError("new_type requires required_field")
```

3. **Add tests:**
```python
# tests/unit/test_models.py
def test_new_event_type():
    event = Event(
        event_type=EventType.NEW_TYPE,
        properties={"required_field": "value"}
    )
    assert event.event_type == EventType.NEW_TYPE
```

4. **Update documentation:**
```markdown
# README.md
## Supported Event Types
- purchase
- user_signup
- page_view
- new_type
```

## Performance Considerations

- Use async/await for I/O operations
- Implement connection pooling
- Add indexes for database queries
- Cache frequently accessed data
- Batch operations when possible

## Security Considerations

- Validate all inputs
- Sanitize user data
- Use parameterized queries
- Implement rate limiting
- Add authentication/authorization
- Use HTTPS in production

## Review Process

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No merge conflicts
- [ ] Changes are focused and minimal

### Review Criteria

Reviewers will check:
- Code quality and readability
- Test coverage
- Documentation completeness
- Performance implications
- Security considerations
- Backward compatibility

## Getting Help

- **Issues:** Create an issue for questions
- **Discussions:** Use GitHub Discussions for general questions
- **Email:** [your-email@example.com]

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be acknowledged in the README.md file.

## Thank You!

Your contributions make EventFlow better for everyone. We appreciate your time and effort!
