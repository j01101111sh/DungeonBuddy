import logging
import secrets
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from dunbud.models import Campaign, HelpfulLink
from dunbud.models.links import MAX_LINKS_PER_CAMPAIGN

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generates helpful links for campaigns."

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting populate_helpful_links")
        try:
            with transaction.atomic():
                self._generate_links()
        except Exception as e:
            logger.exception("Failed to populate helpful links")
            raise e
        self.stdout.write(self.style.SUCCESS("Successfully populated helpful links."))

    def _generate_links(self) -> None:
        campaigns = Campaign.objects.all()
        if not campaigns.exists():
            self.stdout.write(
                self.style.WARNING("No campaigns found. Run populate_campaigns first."),
            )
            return

        secure_random = secrets.SystemRandom()

        link_data = [
            ("D&D Beyond", "https://www.dndbeyond.com"),
            ("Roll20", "https://roll20.net"),
            ("Foundry VTT", "https://foundryvtt.com"),
            ("Kobold Fight Club", "https://koboldplus.club"),
            ("5e Tools", "https://5e.tools"),
            ("Donjon", "https://donjon.bin.sh"),
            ("Fantasy Name Generators", "https://www.fantasynamegenerators.com"),
            ("Inkarnate", "https://inkarnate.com"),
            ("Dungeon Scrawl", "https://probablestrain.itch.io/dungeon-scrawl"),
            ("Token Stamp", "https://rolladvantage.com/tokenstamp/"),
            ("Owlbear Rodeo", "https://www.owlbear.rodeo"),
            ("Discord", "https://discord.com"),
            ("World Anvil", "https://www.worldanvil.com"),
            ("GMBinder", "https://www.gmbinder.com"),
            ("Homebrewery", "https://homebrewery.naturalcrit.com"),
            ("RPGBot", "https://rpgbot.net"),
            ("Sly Flourish", "https://slyflourish.com"),
            ("The Monsters Know", "https://www.themonstersknow.com"),
            ("DMs Guild", "https://www.dmsguild.com"),
            ("DriveThruRPG", "https://www.drivethrurpg.com"),
        ]

        total_created = 0

        for campaign in campaigns:
            current_count = HelpfulLink.objects.filter(campaign=campaign).count()
            if current_count >= MAX_LINKS_PER_CAMPAIGN:
                continue

            # Determine target count (1 to MAX)
            target_count = secure_random.randint(1, MAX_LINKS_PER_CAMPAIGN)

            if current_count >= target_count:
                continue

            needed = target_count - current_count

            # Filter out links already present in this campaign
            existing_names = set(
                HelpfulLink.objects.filter(campaign=campaign).values_list(
                    "name",
                    flat=True,
                ),
            )
            available_samples = [
                (name, url) for name, url in link_data if name not in existing_names
            ]

            # Select random links
            count_to_add = min(needed, len(available_samples))
            selected_samples = secure_random.sample(available_samples, count_to_add)

            new_links = []
            for name, url in selected_samples:
                new_links.append(HelpfulLink(campaign=campaign, name=name, url=url))

            # If we still need more (e.g. we ran out of unique samples), generate generic ones
            remaining = needed - count_to_add
            for _i in range(remaining):
                new_links.append(
                    HelpfulLink(
                        campaign=campaign,
                        name=f"Resource Link {secure_random.randint(1000, 9999)}",
                        url="https://example.com",
                    ),
                )

            HelpfulLink.objects.bulk_create(new_links)
            total_created += len(new_links)

        logger.info("Created %d helpful links.", total_created)
