import logging
import secrets
from typing import Any

from django.core.management.base import BaseCommand

from dunbud.models.campaign import Campaign
from dunbud.models.journal import JournalEntry

logger = logging.getLogger(__name__)

SAMPLE_TITLES = [
    "Reflections on the battle",
    "What a day...",
    "Notes on the strange artifact",
    "We nearly died!",
    "My thoughts on the tavern keeper",
    "A moment of rest",
    "Planning our next move",
    "I don't trust the rogue",
]

SAMPLE_CONTENTS = [
    "Today was exhausting. The goblins were tougher than they looked.",
    "I still can't believe we found that map. It must lead somewhere important.",
    "The wizard is hiding something. I need to keep an eye on them.",
    "We managed to secure the village, but at what cost?",
    "I need to buy more rations before we head into the dungeon.",
    "That riddle was impossible. I'm glad the bard solved it.",
]


class Command(BaseCommand):
    help = "Populates the database with random journal entries for testing."

    def handle(self, *args: Any, **options: Any) -> None:
        campaigns = Campaign.objects.prefetch_related("sessions", "player_characters")
        created_count = 0

        for campaign in campaigns:
            sessions = campaign.sessions.all()
            characters = campaign.player_characters.all()

            for session in sessions:
                for character in characters:
                    # Check if entry already exists to avoid duplicates on re-run
                    if JournalEntry.objects.filter(
                        character=character,
                        session=session,
                    ).exists():
                        continue

                    # 50% chance to create an entry
                    if secrets.choice([True, False]):
                        title = f"{secrets.choice(SAMPLE_TITLES)} (Session {session.session_number})"
                        content = secrets.choice(SAMPLE_CONTENTS)

                        JournalEntry.objects.create(
                            character=character,
                            session=session,
                            title=title,
                            content=content,
                        )
                        created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_count} journal entries.",
            ),
        )
