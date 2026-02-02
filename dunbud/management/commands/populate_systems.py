import logging
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from config.tests.factories import TabletopSystemFactory
from dunbud.models import TabletopSystem

logger = logging.getLogger(__name__)

NUM_SYSTEMS_CREATED = 5


class Command(BaseCommand):
    help = "Generates tabletop systems."

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting populate_systems")
        try:
            with transaction.atomic():
                self._generate_systems()
        except Exception as e:
            logger.exception("Failed to populate systems")
            raise e
        self.stdout.write(self.style.SUCCESS("Successfully populated systems."))

    def _generate_systems(self) -> None:
        if TabletopSystem.objects.exists():
            self.stdout.write("Systems already exist. Skipping creation.")
            return

        for i in range(NUM_SYSTEMS_CREATED):
            TabletopSystemFactory.create(
                name=f"System {i}",
                short_name=f"S#{i}",
            )
        logger.info("Created %d systems.", NUM_SYSTEMS_CREATED)
