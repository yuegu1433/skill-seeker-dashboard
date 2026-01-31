# Skill Management Center Makefile

.PHONY: help install dev run test clean build docker-up docker-down migrate

# Default target
help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  dev         Run development server"
	@echo "  run         Run production server"
	@echo "  test        Run tests"
	@echo "  lint        Run code linting"
	@echo "  format      Format code"
	@echo "  clean       Clean up cache files"
	@echo "  build       Build Docker image"
	@echo "  docker-up   Start Docker compose services"
	@echo "  docker-down Stop Docker compose services"
	@echo "  migrate     Run database migrations"
	@echo "  reset-db    Reset database"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Run development server
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run production server
run:
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Run tests
test:
	pytest tests/ -v --cov=app --cov-report=term-missing

# Run tests with coverage
test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 app/ tests/
	mypy app/

# Format code
format:
	black app/ tests/
	isort app/ tests/

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

# Build Docker image
build:
	docker build -t skill-management-center .

# Start Docker compose services
docker-up:
	docker-compose up -d

# Stop Docker compose services
docker-down:
	docker-compose down

# Restart Docker compose services
docker-restart:
	docker-compose restart

# View Docker compose logs
docker-logs:
	docker-compose logs -f

# Run database migrations
migrate:
	alembic upgrade head

# Create new migration
migrate-create:
	alembic revision --autogenerate -m "Describe changes"

# Reset database
reset-db:
	alembic downgrade base
	alembic upgrade head

# Initialize database
init-db:
	alembic upgrade head

# Check database status
db-status:
	alembic current
	alembic history --verbose

# Create superuser (placeholder)
create-user:
	@echo "Creating superuser..."
	# Add user creation logic here

# Backup database
backup-db:
	pg_dump $(DATABASE_URL) > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Restore database
restore-db:
	psql $(DATABASE_URL) < $(file)

# Health check
health:
	curl -f http://localhost:8000/health || exit 1

# Celery worker
celery-worker:
	celery -A app.tasks.skill_tasks worker --loglevel=info

# Celery beat
celery-beat:
	celery -A app.tasks.skill_tasks beat --loglevel=info

# Celery flower monitoring
celery-flower:
	celery -A app.tasks.skill_tasks flower

# Install development dependencies
install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy

# Run security check
security:
	safety check
	bandit -r app/

# Generate requirements
freeze:
	pip freeze > requirements.txt
