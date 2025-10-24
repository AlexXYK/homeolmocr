# Contributing to olmOCR API

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.10+
- NVIDIA GPU with CUDA support
- Docker and Docker Compose
- Git

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd olmocr-api
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

4. **Run locally**
```bash
python app.py
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small

## Testing

Before submitting a PR:

1. **Test the API**
```bash
python test_api.py path/to/test/image.jpg
```

2. **Test Docker build**
```bash
docker build -t olmocr-api-test .
docker run --gpus all -p 5005:5005 olmocr-api-test
```

3. **Verify health check**
```bash
curl http://localhost:5005/health
```

## Submitting Changes

1. Create a new branch
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Commit with clear messages
```bash
git commit -m "Add: Description of your changes"
```

4. Push to your fork
```bash
git push origin feature/your-feature-name
```

5. Create a Pull Request

## Areas for Contribution

- Performance optimizations
- Additional API endpoints
- Better error handling
- Documentation improvements
- Test coverage
- Security enhancements
- Multi-language support

## Questions?

Open an issue for discussion before starting major changes.

