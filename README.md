# 🎭 api-theatre - Theatre Ticket System 🎫

## Project Description 🌟

`api-theatre` is a powerful REST API built with Django and Django REST Framework for managing theatre performances, reservations, and ticket payments. The project allows you to create, view, and manage plays, theatre halls, actors, genres, reservations, and integrates a payment system via Stripe in test mode for educational purposes. 🚀

This project is ideal for learning backend development, working with Docker, PostgreSQL, and modern API tools like DRF Spectacular for Swagger documentation. 🎨

## Requirements 🛠️

- Docker (already installed, as specified)
- Python 3.13.2 (or higher, installed automatically via Dockerfile)
- Git (optional, for cloning the repository)

## Instructions for Running with Docker 🚢

Follow these steps to deploy and run `api-theatre` locally using Docker Compose. 🐳

### 1. Clone the Repository 📥
If you have access to the repository, clone it:
```bash
git clone https://github.com/valerii-kashpur/api-theatre
cd api-theatre
git checkout dev
```

### 2. Set Up Environment Variables 🗝️
Create a .env file in the project root with settings for PostgreSQL and Stripe. Example .env:
```bash
POSTGRES_DB=theatre_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=#password
POSTGRES_HOST=db
POSTGRES_PORT=5432
DJANGO_SETTINGS_MODULE=service.settings
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
- Replace #password with a secure password.
- Use test Stripe keys (pk_test_ and sk_test_) to simulate payments without real transactions.
- Ensure .env is added to .gitignore to avoid committing it to the repository. 🔒

### 3. Build and Run Containers 🛠️
Use Docker Compose to build and start the project:
```bash
docker-compose up --build
```

- The --build flag rebuilds images if there are changes in Dockerfile or requirements.txt.
- The project will run in the background, and the server will be accessible at http://localhost:8001/. 🌐

### 4. Explore the API with Swagger 🕵️‍♂️
- To view and interact with the API documentation, open your browser and navigate to:
http://localhost:8001/api/doc/swagger/
- Authenticate with a JWT token (obtain the token via authentication endpoints if configured) to test API endpoints, such as /api/theatre/reservations/ for creating reservations or /api/theatre/reservations/{id}/pay/ for simulating payments via Stripe in test mode. 🎉

### 5. Stop and Clean Up Containers 🛑
When finished, stop the containers:
```bash
docker-compose down
```
To completely clean up volumes (e.g., the database), add the --volumes flag:
```bash
docker-compose down --volumes
```

### 6. Additional Commands 🛠️
- Run Tests Inside the Container: Open the container terminal and run:
```bash
docker exec -it api-theatre-theatre-1 bash
python manage.py test
```
- View Logs: Check container logs for debugging:
```bash
docker logs api-theatre-theatre-1
docker logs api-theatre-db-1
```

### Project Structure 📂
- service/ — Project settings and URLs.
- theatre/ — Main app with models, serializers, views, and tests.
- user/ — User and authentication module.
- docker-compose.yml — Docker Compose configuration.
- Dockerfile — Instructions for building the Django application image.
- .env — Environment variables (not included in the repository).

### Contact 📧
For questions or suggestions, contact us at: kashpur.v.f@gmail.com 🦄
