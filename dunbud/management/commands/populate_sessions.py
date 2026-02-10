import logging
import secrets
from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from dunbud.models import Campaign, Session

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Generates a proposed session for each campaign with random player attendance."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting populate_sessions")

        campaigns = (
            Campaign.objects.filter(sessions__isnull=True)
            .select_related("dungeon_master")
            .prefetch_related("players")
        )
        created_count = 0

        secure_random = secrets.SystemRandom()

        for campaign in campaigns:
            # Check if a session already exists to avoid duplicates
            if Session.objects.filter(campaign=campaign).exists():
                continue

            # Create a session scheduled for 7 days from now
            proposed_date = timezone.now() + timedelta(days=7)

            session = Session.objects.create(
                campaign=campaign,
                proposer=campaign.dungeon_master,
                proposed_date=proposed_date,
                duration=4,
            )

            # Randomly determine attendance for each player
            # Statuses: available (attendee), busy (not attendee), no_response (not attendee)
            players = campaign.players.all()
            for player in players:
                status = secure_random.choice(["available", "busy", "no_response"])

                if status == "available":
                    session.attendees.add(player)

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully populated {created_count} sessions."),
        )
        logger.info("Finished populate_sessions")
