import logging
import secrets
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from config.tests.factories import PlayerCharacterFactory
from dunbud.models import Campaign, TabletopSystem

User = get_user_model()
logger = logging.getLogger(__name__)

NUM_DEV_CAMPAIGN_MEMBERS = 4
NUM_DEV_CAMPAIGNS = 5
NUM_JOINED_USER_CAMPAIGNS = 3


class Command(BaseCommand):
    help = "Generates campaigns and associations. Requires users and systems."

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting populate_campaigns")
        try:
            with transaction.atomic():
                self._generate_campaigns()
        except Exception as e:
            logger.exception("Failed to populate campaigns")
            raise e
        self.stdout.write(self.style.SUCCESS("Successfully populated campaigns."))

    def _generate_campaigns(self) -> None:
        # Prerequisites
        systems = list(TabletopSystem.objects.all())
        if not systems:
            raise CommandError("No systems found. Run populate_systems first.")

        dev_user = User.objects.filter(username="dev").first()
        if not dev_user:
            raise CommandError("Dev user not found. Run populate_users first.")

        users = list(User.objects.exclude(username="dev").exclude(is_superuser=True))
        if not users:
            raise CommandError("No test users found. Run populate_users first.")

        secure_random = secrets.SystemRandom()
        user_campaigns = []

        # 1. User Campaigns (Ensure every test user has a campaign)
        for user in users:
            campaign, created = Campaign.objects.get_or_create(
                name=f"Campaign of {user.username}",
                defaults={
                    "dungeon_master": user,
                    "system": secure_random.choice(systems),
                    "description": f"An epic adventure led by {user.username}.",
                    "vtt_link": "https://foundryvtt.com/demo",
                    "video_link": "https://zoom.us/demo",
                },
            )
            user_campaigns.append(campaign)

        # 2. Assign Players (Users joining other User Campaigns)
        for user in users:
            # Filter campaigns where this user is NOT the DM
            valid_campaigns = [c for c in user_campaigns if c.dungeon_master != user]

            if len(valid_campaigns) >= NUM_JOINED_USER_CAMPAIGNS:
                # Get random campaigns to join
                # We check if they are already a player to avoid duplicates
                current_joined = [
                    c for c in valid_campaigns if c.players.contains(user)
                ]
                needed = NUM_JOINED_USER_CAMPAIGNS - len(current_joined)

                if needed > 0:
                    candidates = [
                        c for c in valid_campaigns if not c.players.contains(user)
                    ]
                    selected_campaigns = secure_random.sample(
                        candidates,
                        min(needed, len(candidates)),
                    )

                    for campaign in selected_campaigns:
                        campaign.players.add(user)
                        PlayerCharacterFactory.create(
                            user=user,
                            campaign=campaign,
                            name=f"{user.username}'s Character",
                        )

        # 3. Add Dev User to User Campaigns
        for campaign in user_campaigns:
            if not campaign.players.contains(dev_user):
                campaign.players.add(dev_user)
                PlayerCharacterFactory.create(
                    user=dev_user,
                    campaign=campaign,
                    name="Dev's Hero",
                )

        # 4. Dev Campaigns
        for i in range(1, NUM_DEV_CAMPAIGNS + 1):
            campaign, created = Campaign.objects.get_or_create(
                name=f"Dev Adventure {i}",
                defaults={
                    "dungeon_master": dev_user,
                    "system": secure_random.choice(systems),
                    "description": "A canonical adventure run by the Developer.",
                    "vtt_link": "https://foundryvtt.com/demo",
                    "video_link": "https://zoom.us/demo",
                },
            )

            current_players_count = campaign.players.count()
            needed = NUM_DEV_CAMPAIGN_MEMBERS - current_players_count

            if needed > 0:
                potential_players = [
                    u for u in users if not campaign.players.contains(u)
                ]
                if len(potential_players) >= needed:
                    selected = secure_random.sample(potential_players, needed)
                    campaign.players.add(*selected)
                    for p in selected:
                        PlayerCharacterFactory.create(
                            user=p,
                            campaign=campaign,
                        )

        logger.info("Campaigns and characters populated.")
