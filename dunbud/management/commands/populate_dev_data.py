import logging
from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to populate the database with development data.
    This is a wrapper that calls individual population commands.
    """

    help = "Generates all development data: systems, users, campaigns, and blog posts."

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Executes the data generation process by calling sub-commands.
        """
        self.stdout.write("Starting full data generation...")
        logger.info("Starting populate_dev_data command")

        try:
            call_command("populate_systems")
            call_command("populate_users")
            call_command("populate_campaigns")
            call_command("populate_blog")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error generating data: {e}"))
            raise e

        self.stdout.write(
            self.style.SUCCESS("Successfully generated all development data."),
        )
        logger.info("Finished populate_dev_data command")
