# Build and Run with Docker

```bash
# Build the Docker images
docker-compose build

# Start the services
docker-compose up -d

# Check if services are running
docker-compose ps
```


# Initialize the Database

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create a superuser for admin access
docker-compose exec web python manage.py createsuperuser

# Follow the prompts to create admin account

```

# Application Access

- Web Application: http://localhost:8000
- Admin Panel: http://localhost:8000/admin

# Run Tests

```bash 
# Run all tests
docker-compose exec web pytest

# Run AI integration test
docker-compose exec web python test_ai_integration.py
```

# View Logs

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs web
docker-compose logs db
```

# Stop the Application

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes (database data)
docker-compose down -v
```