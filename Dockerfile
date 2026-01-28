# Use the official uv image with Python 3.14
FROM ghcr.io/astral-sh/uv:python3.14-bookworm

# Install system dependencies (if any are needed for your specific packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Configure env
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PORT=8000

WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Sync dependencies (creates .venv)
# --frozen: requires uv.lock to be up to date
# --no-install-project: only installs dependencies, not the app itself yet
# --no-dev: excludes dev dependencies like pytest/ruff
RUN uv sync --frozen --no-install-project --no-dev --group prod

# Copy the rest of the application code
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev --group prod

# Collect static files
# We use a dummy secret key here because the build step shouldn't need the real one,
# but Django throws an error if it's missing.
RUN SECRET_KEY=dummy-key-for-build uv run python manage.py collectstatic --noinput

# Expose the port
EXPOSE 8000

# Run with Gunicorn
CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
