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
        from django.db.models import Count

        # It's good practice to move this to a module-level constant
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

        campaigns = Campaign.objects.annotate(
            link_count=Count("helpful_links"),
        ).filter(link_count__lt=MAX_LINKS_PER_CAMPAIGN)

        if not campaigns.exists():
            self.stdout.write(
                self.style.WARNING(
                    "No campaigns found needing links, or all are full. Run populate_campaigns first.",
                ),
            )
            return

        secure_random = secrets.SystemRandom()

        # Pre-fetch all existing link names to avoid N+1 queries
        existing_links_qs = HelpfulLink.objects.values("campaign_id", "name")
        links_by_campaign: dict[Any, Any] = {}
        for link in existing_links_qs:
            links_by_campaign.setdefault(link["campaign_id"], set()).add(link["name"])
        logger.warning(existing_links_qs)

        links_to_create = []
        for campaign in campaigns:
            current_count = campaign.link_count

            target_count = secure_random.randint(1, MAX_LINKS_PER_CAMPAIGN)
            if current_count >= target_count:
                continue

            needed = target_count - current_count

            existing_names = links_by_campaign.get(campaign.id, set())
            available_samples = [
                (name, url) for name, url in link_data if name not in existing_names
            ]

            count_to_add = min(needed, len(available_samples))
            selected_samples = secure_random.sample(available_samples, count_to_add)
            for name, url in selected_samples:
                links_to_create.append(
                    HelpfulLink(campaign=campaign, name=name, url=url),
                )

            remaining = needed - count_to_add
            for _i in range(remaining):
                links_to_create.append(
                    HelpfulLink(
                        campaign=campaign,
                        name=f"Resource Link {secure_random.randint(1000, 9999)}",
                        url="https://example.com",
                    ),
                )

        if links_to_create:
            HelpfulLink.objects.bulk_create(links_to_create)

        logger.info("Created %d helpful links.", len(links_to_create))
