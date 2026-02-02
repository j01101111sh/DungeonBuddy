import logging
from typing import Any

from blog.models import Post
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generates blog posts."

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting populate_blog")
        try:
            with transaction.atomic():
                self._generate_posts()
        except Exception as e:
            logger.exception("Failed to populate blog")
            raise e
        self.stdout.write(self.style.SUCCESS("Successfully populated blog."))

    def _generate_posts(self) -> None:
        dev_user = User.objects.filter(username="dev").first()
        if not dev_user:
            raise CommandError("Dev user not found. Run populate_users first.")

        blog_posts_data = [
            {
                "title": "Welcome to Dungeon Buddy!",
                "slug": "welcome-dungeon-buddy",
                "content": "We're excited to launch the **beta** version of Dungeon Buddy! Manage your campaigns and characters with ease.",
                "is_published": True,
            },
            {
                "title": "New Feature: Dice Roller",
                "slug": "new-feature-dice-roller",
                "content": "You can now roll dice directly in your campaign chat. Try `/roll 2d20`!",
                "is_published": True,
            },
            {
                "title": "Draft: Future Roadmap",
                "slug": "draft-future-roadmap",
                "content": "This is a sneak peek at what we are building next. *Not for public release yet.*",
                "is_published": False,
            },
        ]

        for post_data in blog_posts_data:
            Post.objects.get_or_create(
                slug=post_data["slug"],
                defaults={
                    "title": post_data["title"],
                    "content": post_data["content"],
                    "author": dev_user,
                    "is_published": post_data["is_published"],
                },
            )
        logger.info("Created %d blog posts.", len(blog_posts_data))
