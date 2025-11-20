# Dataflow 🔄

A FastAPI-based application for transferring data between databases with visual flow representation.

## Features

- 🚀 **High-Performance Data Transfer**: Transfer data between databases efficiently using batch processing
- 📊 **Visual Flow Diagrams**: Interactive Sankey diagrams showing data flow between databases
- 🔒 **Security First**: Comprehensive security scanning with SAST, SBOM, and dependency checks
- 🎯 **RESTful API**: Clean, well-documented API endpoints using FastAPI
- 📝 **Automatic Documentation**: Interactive API documentation via Swagger UI
- 🔍 **Transfer Tracking**: Monitor transfer status and history

## Quick Start

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/kelleyblackmore/Dataflow.git
cd Dataflow
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize sample databases:
```bash
python -m app.main
```

### Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## API Endpoints

### Health Check
```http
GET /health
```
Check if the service is running.

### Initialize Sample Data
```http
POST /databases/initialize
```
Create sample databases with test data for demonstration.

### Transfer Data
```http
POST /transfer
Content-Type: application/json

{
  "source_db": "source",
  "destination_db": "destination",
  "source_table": "users",
  "destination_table": "users_copy",
  "batch_size": 1000
}
```

### Get Transfer Status
```http
GET /transfer/status/{transfer_id}
```

### Visualize Data Flow
```http
GET /flow/visualize
```
View an interactive diagram of data flows.

### List Databases
```http
GET /databases/list
```

## Example Usage

1. **Initialize sample databases**:
```bash
curl -X POST http://localhost:8000/databases/initialize
```

2. **Transfer data**:
```bash
curl -X POST http://localhost:8000/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "source_db": "source",
    "destination_db": "destination",
    "source_table": "users",
    "destination_table": "users_copy",
    "batch_size": 1000
  }'
```

3. **View the flow diagram**:
Open http://localhost:8000/flow/visualize in your browser.

## Project Structure

```
Dataflow/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and routes
│   ├── models.py            # Pydantic models
│   ├── database.py          # Database management
│   ├── transfer.py          # Data transfer logic
│   └── visualization.py     # Flow diagram generation
├── .github/
│   └── workflows/
│       ├── lint.yml         # Linting workflow
│       ├── sast.yml         # Static security testing
│       ├── sbom.yml         # Software bill of materials
│       └── security.yml     # Security scanning
├── requirements.txt         # Python dependencies
└── README.md
```

## GitHub Actions Workflows

This project includes comprehensive CI/CD workflows:

### 🧹 Linting (`lint.yml`)
- **Black**: Code formatting check
- **Flake8**: Style guide enforcement (PEP 8)
- **Pylint**: Code quality analysis
- **MyPy**: Static type checking

### 🔒 SAST - Static Application Security Testing (`sast.yml`)
- **Bandit**: Python security linter
- **CodeQL**: Semantic code analysis
- **Safety**: Dependency vulnerability scanning

### 📦 SBOM - Software Bill of Materials (`sbom.yml`)
- **CycloneDX**: SBOM generation (JSON/XML formats)
- **pip-audit**: Vulnerability detection in dependencies
- **Dependency Review**: PR-based dependency analysis

### 🛡️ Security Scanning (`security.yml`)
- **OWASP Dependency-Check**: Comprehensive dependency analysis
- **Trivy**: Vulnerability scanner for containers and filesystems
- **Gitleaks**: Secret detection in code

All workflows run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Scheduled scans (weekly for security)

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type annotations
- **Plotly**: Interactive visualization library
- **Uvicorn**: ASGI server implementation
- **aiosqlite**: Async SQLite database driver

## Security

This project implements multiple layers of security:

1. **Static Analysis**: Bandit and CodeQL scan for security vulnerabilities
2. **Dependency Scanning**: Safety, OWASP, and Trivy check for known vulnerabilities
3. **Secret Detection**: Gitleaks prevents committing sensitive information
4. **SBOM Generation**: Track all dependencies for supply chain security
5. **Regular Scans**: Automated weekly security scans

## Development

### Running Linters Locally

```bash
# Install linting tools
pip install flake8 black pylint mypy bandit

# Format code
black app/

# Check style
flake8 app/

# Static analysis
pylint app/

# Type checking
mypy app/

# Security check
bandit -r app/
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests with coverage
pytest --cov=app tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

All pull requests will automatically run through linting, security scanning, and SBOM generation.

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

Built with ❤️ using FastAPI and Python