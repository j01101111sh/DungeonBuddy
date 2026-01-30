import logging
import secrets
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from config.tests.factories import TabletopSystemFactory
from dunbud.models import Campaign, TabletopSystem

# Get the custom user model
User = get_user_model()

# Configure logging
logger = logging.getLogger(__name__)

# Constants for script config
NUM_DEV_CAMPAIGN_MEMBERS = 4
NUM_DEV_CAMPAIGNS = 5
NUM_JOINED_USER_CAMPAIGNS = 3
NUM_SYSTEMS_CREATED = 5
NUM_TEST_USERS = 20


class Command(BaseCommand):
    """
    Management command to populate the database with development data.

    Generates:
    - NUM_TEST_USERS Test Users.
    - NUM_TEST_USERS Campaigns (1 per test user as DM).
    - NUM_DEV_CAMPAIGNS Dev Campaigns (Dev user as DM).

    Associations:
    - Each test user joins NUM_JOINED_USER_CAMPAIGNS other test-user campaigns as a player.
    - The 'dev' user joins ALL NUM_TEST_USERS test-user campaigns as a player.
    - Each 'Dev Campaign' has NUM_DEV_CAMPAIGN_MEMBERS random test users as players.
    """

    help = (
        "Generates development data: users, campaigns, and complex party associations."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Executes the data generation process.
        """
        self.stdout.write("Starting data generation...")
        logger.info("Starting populate_dev_data command")

        try:
            with transaction.atomic():
                self._generate_data()
        except Exception as e:
            logger.exception("Failed to generate data")
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
        # 0. Retrieve or Create the 'dev' user
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
        if not dev_user.is_staff:
            dev_user.is_staff = True
            dev_user.save()

        # 1. Initialize common variables
        systems = list(TabletopSystem.objects.all())

        if not systems:
            for i in range(NUM_SYSTEMS_CREATED):
                system_created = TabletopSystemFactory.create(
                    name=f"System {i}",
                    short_name=f"S#{i}",
                )
                systems.append(system_created)

        users = []
        user_campaigns: list[Campaign] = []
        secure_random = secrets.SystemRandom()

        # 2. Create 20 Test Users
        for i in range(1, NUM_TEST_USERS + 1):
            username = f"user_{i}"
            email = f"user_{i}@example.com"
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

        # 3. Create Campaigns (1 per test user as DM)
        for user in users:
            campaign_name = f"Campaign of {user.username}"
            campaign, created = Campaign.objects.get_or_create(
                name=campaign_name,
                defaults={
                    "dungeon_master": user,
                    "system": secure_random.choice(systems),
                    "description": f"An epic adventure led by {user.username}.",
                    "vtt_link": "https://foundryvtt.com/demo",
                    "video_link": "https://zoom.us/demo",
                },
            )
            user_campaigns.append(campaign)

        # 4. Assign Players to User Campaigns
        for i, user in enumerate(users):
            # A. Each test user joins some campaigns they do not DM.
            available_indices = [x for x in range(len(user_campaigns)) if x != i]
            selected_indices = secure_random.sample(
                available_indices,
                NUM_JOINED_USER_CAMPAIGNS,
            )

            for idx in selected_indices:
                target_campaign = user_campaigns[idx]
                target_campaign.players.add(user)

        # 5. Add Dev User to ALL User Campaigns
        for campaign in user_campaigns:
            campaign.players.add(dev_user)

        logger.info(
            "Dev user 'dev' added to all %d user campaigns.",
            len(user_campaigns),
        )

        # 6. Create Campaigns with Dev User as DM
        dev_campaigns = []
        for i in range(1, NUM_DEV_CAMPAIGNS + 1):
            campaign_name = f"Dev Adventure {i}"
            campaign, created = Campaign.objects.get_or_create(
                name=campaign_name,
                defaults={
                    "dungeon_master": dev_user,
                    "system": secure_random.choice(systems),
                    "description": "A canonical adventure run by the Developer.",
                    "vtt_link": "https://foundryvtt.com/demo",
                    "video_link": "https://zoom.us/demo",
                },
            )
            dev_campaigns.append(campaign)

            # Assign random users as players
            selected_players = secure_random.sample(users, NUM_DEV_CAMPAIGN_MEMBERS)
            campaign.players.add(*selected_players)
            logger.debug(
                "Created Dev campaign '%s' with %d players.",
                campaign_name,
                len(selected_players),
            )

        logger.info(
            "Generated %d users, %d user campaigns, and %d dev campaigns.",
            len(users),
            len(user_campaigns),
            len(dev_campaigns),
        )
