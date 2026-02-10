import secrets

from django.utils import timezone

from ..models import Campaign, Session, TabletopSystem


class CampaignFactory:
    """Factory for creating Campaign instances for testing."""

    @staticmethod
    def create(**kwargs):
        """Create a Campaign instance."""
        if "name" not in kwargs:
            kwargs["name"] = f"Campaign {secrets.token_hex(4)}"
        if "system" not in kwargs:
            # Assumes at least one TabletopSystem exists or creates one.
            # In a real test setup, you might want to ensure this dependency is handled.
            system, _ = TabletopSystem.objects.get_or_create(
                name="D&D 5e",
                defaults={"short_name": "5e"},
            )
            kwargs["system"] = system
        return Campaign.objects.create(**kwargs)


class SessionFactory:
    """Factory for creating Session instances for testing."""

    @staticmethod
    def create(**kwargs):
        """Create a Session instance."""
        if "proposed_date" not in kwargs:
            kwargs["proposed_date"] = timezone.now()
        if "duration" not in kwargs:
            kwargs["duration"] = 3
        return Session.objects.create(**kwargs)
