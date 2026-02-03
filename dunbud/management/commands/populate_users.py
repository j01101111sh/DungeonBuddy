import logging
from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from config.tests.factories import UserFactory

User = get_user_model()
logger = logging.getLogger(__name__)

NUM_TEST_USERS = 20


class Command(BaseCommand):
    help = "Generates dev user and test users."

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting populate_users")
        try:
            with transaction.atomic():
                self._generate_users()
        except Exception as e:
            logger.exception("Failed to populate users")
            raise e
        self.stdout.write(self.style.SUCCESS("Successfully populated users."))

    def _generate_users(self) -> None:
        # Dev User
        if not User.objects.filter(username="dev").exists():
            _, dev_pass = UserFactory.create(
                username="dev",
                is_staff=True,
                is_superuser=False,
            )

            file_path = Path(".devpass")
            with file_path.open("w") as f:
                f.write(dev_pass)
        elif existing_dev_user := User.objects.filter(username="dev").first():
            existing_dev_user.is_staff = True
            existing_dev_user.save()

        # Test Users
        # We exclude the dev user to count only test users
        current_count = User.objects.exclude(username="dev").count()
        needed = NUM_TEST_USERS - current_count
        if needed > 0:
            for _ in range(needed):
                UserFactory.create()
            logger.info("Created %d test users.", needed)
        else:
            self.stdout.write("Enough test users exist.")
