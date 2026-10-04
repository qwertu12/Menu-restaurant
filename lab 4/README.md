# FastAPI Lab 4

## First run after Lab 3

This lab changes the database schema and requires a clean PostgreSQL volume.

```cmd
docker compose down -v
docker compose up -d
uv sync
cd app
uv run alembic upgrade head
uv run python main.py
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Main authentication flow

1. `POST /api/auth/register`
2. `POST /api/auth/login`
3. Click `Authorize` in Swagger and log in with the same email/password.
4. Create a recipe with `POST /api/recipes`.
5. `GET /api/recipes` or `GET /api/recipes/{id}` returns the recipe author.
6. Updating and deleting require authentication and are allowed only for the recipe author.
