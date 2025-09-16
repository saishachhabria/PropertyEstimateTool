# Valora Earth Property Estimate Tool

## Overview

A Django-based web application that generates AI-powered financial projections for regenerative agriculture projects. Users input property details, complete a questionnaire, and receive comprehensive 10-year financial projections.

## Project Structure

```
property-estimate-tool/
├── estimate/               # Main Django application
│   ├── migrations/         # Database migrations
│   ├── tests/              # Test suite
        ├── test_ai_service.py    # Tests for AI functions
        ├── test_models.py  # Tests for models
        └── test_views.py   # Tests for views
│   ├── admin.py            # Django admin configuration
│   ├── ai_service.py       # AI service integration
│   ├── forms.py            # Django forms
│   ├── models.py           # Database models
│   ├── urls.py             # URL routing
│   └── views.py            # View controllers
├── property_tool/          # Django project settings
│   ├── settings.py         # Project configuration
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py             # WSGI application
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── form.html           # Landing page form
│   ├── questionnaire.html  # Questionnaire interface
│   ├── waiting.html        # Processing page
│   └── results.html        # Results display
├── static/                 # Static assets
│   └── images/             # Image assets
├── Dockerfile              # Container definition
├── docker-compose.yml      # Docker orchestration
├── requirements.txt        # Python dependencies
├── pytest.ini              # Test configuration
├── README.md               # Project description
├── TESTING.md              # Test Setup
├── DOCKER.md               # Docker Setup
└── manage.py               # Django management script
```

## Installation

### Prerequisites

- Python 3.11+
- pip
- PostgreSQL (optional for production)
- Docker and Docker Compose (for containerized deployment)

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/saishachhabria/PropertyEstimateTool
cd property-estimate-tool
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env    # Edit .env variables
```

5. Run database migrations:
```bash
python manage.py migrate
```

6. Create superuser for admin access:
```bash
python manage.py createsuperuser
```

7. Collect static files:
```bash
python manage.py collectstatic --noinput
```

8. Run development server:
```bash
python manage.py runserver
```

Access the application at `http://localhost:8000`

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DATABASE_URL=sqlite:///db.sqlite3  # For development

# OpenAI API (optional - uses mock service if not provided)
OPENAI_API_KEY=sk-your-api-key
USE_MOCK_AI=False
```

### Database Configuration

Configured in `settings.py`:

```python
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
    )
}
```

## Usage

### User Flow

1. **Property Details**: Users enter property address and lot size
2. **Questionnaire**: Four-question survey about goals and current situation
3. **Processing**: AI generates financial projections
4. **Results**: Interactive dashboard with charts and data tables

### Admin Interface

Access Django admin at `http://localhost:8000/admin`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/estimate/` | GET/POST | Property estimate form |
| `/estimate/questionnaire/<id>/<question>/` | GET/POST | Questionnaire flow |
| `/estimate/processing/<id>/` | GET | Processing status page |
| `/estimate/generate/<id>/` | POST | Generate estimate (AJAX) |
| `/estimate/results/<id>/` | GET | View results |
| `/estimate/health/` | GET | Health check endpoint |

## Development

### Code Style

PEP 8:
```bash
# Format code
black estimate/

# Check linting
flake8 estimate/
```

### Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

### Static Files

```bash
python manage.py collectstatic
python manage.py runserver --insecure
```

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
lsof -i :8000 # Find process using port 8000
kill -9 <PID> # Kill process
```

**Static files not loading:**
```bash
python manage.py collectstatic --clear --noinput
```

**OpenAI API errors:**
- Verify API key is valid
- Check account has credits
- System automatically falls back to mock service
