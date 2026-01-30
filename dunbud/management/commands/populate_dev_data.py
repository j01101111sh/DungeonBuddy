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
    Creates 20 users and 20 campaigns.
    Every user is a DM for 1 campaign and a player in 3 other campaigns.
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
            logger.error("Failed to generate data: %s", e)
            self.stdout.write(self.style.ERROR(f"Error generating data: {e}"))
            raise e

        self.stdout.write(
            self.style.SUCCESS("Successfully generated development data."),
        )
        logger.info("Finished populate_dev_data command")

    def _generate_data(self) -> None:
        """
        Internal method to handle the creation logic to ensure atomicity.
        """
        # 1. Ensure a TabletopSystem exists
        system, _ = TabletopSystem.objects.get_or_create(
            name="Dungeons & Dragons 5e",
            defaults={"description": "The world's greatest roleplaying game."},
        )

        users = []
        campaigns = []
        secure_random = secrets.SystemRandom()

        # 2. Create 20 Users
        for i in range(1, 21):
            username = f"user_{i}"
            email = f"user_{i}@example.com"
            # In a real scenario, use a secure password. For dev data, a known pattern is often useful.
            # Using secrets to generate a random component for the password to satisfy requirements.
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

        # 3. Create 20 Campaigns (1 per user as DM)
        for _, user in enumerate(users):
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

        # 4. Assign Players (Each user joins 3 campaigns they do not DM)
        for i, user in enumerate(users):
            # The user DMs the campaign at index i.
            # We need to pick 3 indices from 0..19 excluding i.
            available_indices = [x for x in range(len(campaigns)) if x != i]

            # Use secrets.SystemRandom for secure choice (prefer secrets over random)
            selected_indices = secure_random.sample(available_indices, 3)

            for idx in selected_indices:
                campaign = campaigns[idx]
                campaign.players.add(user)
                logger.debug("User %s joined campaign %s", user.username, campaign.name)

        logger.info(
            "Generated %d users and %d campaigns with associations.",
            len(users),
            len(campaigns),
        )
