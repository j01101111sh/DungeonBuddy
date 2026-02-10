# Project Overview

This is a Django project called "Dungeon Buddy". Based on the file structure and dependencies, it appears to be a web application for managing Dungeons & Dragons campaigns.

**Main Technologies:**

*   **Backend:** Django
*   **Frontend:** HTML, CSS, JavaScript (with Bootstrap 5 for styling)
*   **Database:** PostgreSQL or SQLite
*   **Deployment:** Gunicorn, Whitenoise

**Project Structure:**

The project is divided into three main Django apps:

*   `dunbud`: The core application for managing campaigns.
*   `users`: Handles user authentication and profiles.
*   `blog`: A blog for project updates or related content.

# Key Architecture Decisions

* **Identifiers:** All primary models (`Campaign`, `PlayerCharacter`, etc.) use `UUID` fields as primary keys instead of incremental integers to prevent enumeration attacks and facilitate easier data migration.
* **User Model:** The project uses a custom user model (`users.CustomUser`) as recommended by Django best practices.
* **Configuration:** Environment variables are loaded via `python-dotenv`.
* **Logging:** The application is configured to log to the `logs/` directory.

# Development Setup

This project includes a `dev_setup.sh` script that automates the setup of a development environment. To use it, run the following command:

```bash
bash dev_setup.sh
```

This script will:

1.  Install all dependencies using `uv`.
2.  Install pre-commit hooks.
3.  Create a `.env` file with a new `SECRET_KEY` if it doesn't exist.
4.  Run database migrations.
5.  Create a superuser and a regular user for development.
6.  Create a cache table.
7.  Populate the database with development data.
8.  Verify the setup.

After the script finishes, you can run the development server with:

```bash
uv run python manage.py runserver
```

# Development Conventions

*   The project uses `crispy-forms` and `crispy-bootstrap5` for form rendering.
*   Static files are managed by `whitenoise`.
*   The project follows standard Django development practices.

## Linting

This project uses `ruff` for linting and formatting. To check for linting errors, run:

```bash
uv run ruff check --force-exclude --fix
```

To format the code, run:

```bash
uv run ruff format --force-exclude
```

## Type Checking

This project uses `mypy` for static type checking. To run the type checker, use the following command:

```bash
uv run mypy --strict
```

## Testing

This project uses `pytest` for testing. To run the test suite, use the following command:

```bash
uv run pytest
```

The test configuration is located in the `pyproject.toml` file under the `[tool.pytest.ini_options]` section.

Tests in this project are written as `django.test.TestCase` subclasses, using `setUp` methods for test setup rather than standalone pytest fixtures.

Object factories to be used for testing purposes should be kept in config/tests/factories.py and should follow the style of the factories already there. Factories should be used whenever possible in testing.
