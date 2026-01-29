# Use the official uv image with Python 3.14
FROM ghcr.io/astral-sh/uv:python3.14-bookworm

# Install system dependencies (if any are needed for your specific packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Railway setup
ARG SECRET_KEY
ARG PROJ_NAME="config"

# Configure env
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PORT=8000 \
    SECRET_KEY=$SECRET_KEY

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

# Expose the port
EXPOSE 8000

# Collect static files
RUN uv run python manage.py collectstatic --noinput

# create a bash script to run the Django project
# this script will execute at runtime when
# the container starts and the database is available
RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./paracord_runner.sh && \
    printf "uv run python manage.py migrate --no-input\n" >> ./paracord_runner.sh && \
    printf "uv run gunicorn ${PROJ_NAME}.wsgi:application --bind \"[::]:\$RUN_PORT\"\n" >> ./paracord_runner.sh

# make the bash script executable
RUN chmod +x paracord_runner.sh

# Clean up apt cache to reduce image size
RUN apt-get remove --purge -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Run with Gunicorn
# Run the Django project via the runtime script
# when the container starts
CMD ./paracord_runner.sh
