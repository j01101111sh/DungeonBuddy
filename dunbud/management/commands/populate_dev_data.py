import logging
import secrets
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from dunbud.models import Campaign, TabletopSystem

# Get the custom user model
User = get_user_model()

# Configure logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to populate the database with development data.

    Generates:
    - 20 Users (test users).
    - 20 Campaigns (1 per test user as DM).
    - Associations:
        - Each test user joins 3 other campaigns as a player.
        - The 'dev' user joins ALL 20 campaigns as a player.
    """

    help = "Generates development data: 20 users, 20 campaigns, and party associations."

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Executes the data generation process.

        Args:
            *args: Variable length argument list.
            **options: Arbitrary keyword arguments.
        """
        self.stdout.write("Starting data generation...")
        logger.info("Starting populate_dev_data command")

        try:
            with transaction.atomic():
                self._generate_data()
        except Exception as e:
            logger.exception("Failed to generate data")
            self.stdout.write(self.style.ERROR(f"Error generating data: {e}"))
            # Re-raise to ensure non-zero exit code if run in CI/CD or scripts
            raise e

        self.stdout.write(
            self.style.SUCCESS("Successfully generated development data."),
        )
        logger.info("Finished populate_dev_data command")

    def _generate_data(self) -> None:
        """
        Internal method to handle the creation logic to ensure atomicity.
        """
        # 0. Retrieve or Create the 'dev' user
        # We assume dev_setup.sh created it, but we get_or_create to be safe.
        dev_user, _ = User.objects.get_or_create(
            username="dev",
            defaults={
                "email": "dev@dev.com",
                "is_staff": True,
                "is_superuser": False,
            },
        )
        if not dev_user.has_usable_password():
            dev_user.set_password("dev")
            dev_user.save()

        # 1. Ensure a TabletopSystem exists
        system, _ = TabletopSystem.objects.get_or_create(
            name="Dungeons & Dragons 5e",
            defaults={"description": "The world's greatest roleplaying game."},
        )

        users = []
        campaigns: list[Campaign] = []
        secure_random = secrets.SystemRandom()

        # 2. Create 20 Test Users
        for i in range(1, 21):
            username = f"user_{i}"
            email = f"user_{i}@example.com"
            # Secure random suffix for password, though strictly not necessary for dev data, it's good practice.
            password_suffix = secrets.token_hex(4)
            password = f"password_{i}_{password_suffix}"

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "bio": f"Bio for {username}. I love TTRPGs!",
                    "location": "Internet",
                },
            )
            if created:
                user.set_password(password)
                user.save()
                logger.debug("Created user: %s", username)
            users.append(user)

        # 3. Create 20 Campaigns (1 per test user as DM)
        for _i, user in enumerate(users):
            campaign_name = f"Campaign of {user.username}"
            campaign, created = Campaign.objects.get_or_create(
                name=campaign_name,
                defaults={
                    "dungeon_master": user,
                    "system": system,
                    "description": f"An epic adventure led by {user.username}.",
                    "vtt_link": "https://foundryvtt.com/demo",
                    "video_link": "https://zoom.us/demo",
                },
            )
            if created:
                logger.debug(
                    "Created campaign: %s (DM: %s)",
                    campaign_name,
                    user.username,
                )
            campaigns.append(campaign)

        # 4. Assign Players
        for i, user in enumerate(users):
            # A. Each test user joins 3 campaigns they do not DM.
            # We need to pick 3 indices from 0..19 excluding i.
            available_indices = [x for x in range(len(campaigns)) if x != i]

            # Use secrets.SystemRandom for secure choice
            selected_indices = secure_random.sample(available_indices, 3)

            for idx in selected_indices:
                target_campaign = campaigns[idx]
                target_campaign.players.add(user)
                logger.debug(
                    "User %s joined campaign %s",
                    user.username,
                    target_campaign.name,
                )

        # 5. Add Dev User to ALL Campaigns
        for campaign in campaigns:
            campaign.players.add(dev_user)

        logger.info("Dev user 'dev' added to all %d campaigns.", len(campaigns))

        logger.info(
            "Generated %d users and %d campaigns with associations.",
            len(users),
            len(campaigns),
        )
