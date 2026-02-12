#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SU_NAME="admin"
SU_EMAIL="admin@example.com"
SU_PASSWORD="admin"

DEV_NAME="dev"
DEV_EMAIL="dev@dev.com"
DEV_PASSWORD="dev"

# 0. Delete existing dev files
echo -e "${YELLOW}Deleting existing dev files...${NC}"
rm db.sqlite3 .coverage .devpass coverage.xml db.sqlite-journal
rm -Rf logs/ htmlcov/ staticfiles/

# 1. Sync Dependencies (uv)
echo -e "${CYAN}Syncing dependencies with uv...${NC}"
uv sync

# 2. Install pre-commit hooks
echo -e "${CYAN}Installing pre-commit hooks...${NC}"
uv run pre-commit install --install-hooks

# 3. Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}.env file not found. Generating new file with Django SECRET_KEY...${NC}"
    echo "SECRET_KEY=$(uv run python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" > .env
    echo -e "${YELLOW}Setting DEBUG to True for dev environments...${NC}"
    echo "DEBUG=True" >> .env
    echo "TEMPLATE_DEBUG=True" >> .env
    echo "CSRF_TRUSTED_ORIGINS=https://localhost:8000,https://*.github.dev,https://*.app.github.dev" >> .env
    echo "ADMIN_URL=admin/" >> .env
    echo "ALLOWED_HOSTS=*" >> .env
    echo "LOG_LEVEL=INFO" >> .env
    echo -e "${GREEN}Done: .env created.${NC}"
else
    echo -e "${GREEN}.env file already exists. Skipping generation.${NC}"
fi

# 4. Run Django migrations
echo -e "${CYAN}Running database migrations...${NC}"
uv run python manage.py migrate

# 5a. Create Superuser (Idempotent)
echo -e "${CYAN}Checking for superuser...${NC}"
uv run python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='$SU_NAME').exists():
    User.objects.create_superuser('$SU_NAME', '$SU_EMAIL', '$SU_PASSWORD');
    print('\033[0;32mSuperuser created successfully.\033[0m');
else:
    print('\033[0;32mSuperuser already exists. Skipping creation.\033[0m');
"

# 5b. Create Dev User (Idempotent)
echo -e "${CYAN}Checking for dev user...${NC}"
uv run python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='$DEV_NAME').exists():
    User.objects.create_user('$DEV_NAME', '$DEV_EMAIL', '$DEV_PASSWORD');
    print('\033[0;32mDev user created successfully.\033[0m');
else:
    print('\033[0;32mDev user already exists. Skipping creation.\033[0m');
"

# 6. Set up cache table
echo -e "${CYAN}Creating cache table...${NC}"
uv run python manage.py createcachetable

# 7. Populate Development Data
echo -e "${CYAN}Populating development data...${NC}"
uv run python manage.py populate_dev_data

# 8. Verify Setup
echo -e "${CYAN}Verifying setup...${NC}"
uv run python manage.py check

echo -e "${GREEN}Setup complete.${NC}"
echo -e "Run the server with: ${CYAN}uv run python manage.py runserver${NC}"
