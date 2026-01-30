import secrets
from typing import Any

from django.contrib.auth import get_user_model

from dunbud.models import TabletopSystem
from users.models import CustomUser

# Type alias for the user model
User = get_user_model()


class UserFactory:
    """
    Factory for creating Django User instances for testing purposes.
    """

    @staticmethod
    def create(
        password: str | None = None,
        **kwargs: Any,
    ) -> tuple[CustomUser, str]:
        """
        Creates a new user instance.

        Args:
            password: The password to set. If None, a random URL-safe string is generated.
            **kwargs: Additional fields for the user (e.g., username, email).

        Returns:
            A tuple containing (user_instance, plain_text_password).
        """
        if "username" not in kwargs:
            kwargs["username"] = f"user_{secrets.token_hex(4)}"

        if "email" not in kwargs:
            kwargs["email"] = f"{kwargs['username']}@example.com"

        plain_password = password or secrets.token_urlsafe(16)
        user = User.objects.create_user(password=plain_password, **kwargs)  # type: ignore

        return user, plain_password


class TabletopSystemFactory:
    """
    Factory for creating Django TabletopSystem instances for testing purposes.
    """

    @staticmethod
    def create(
        **kwargs: Any,
    ) -> TabletopSystem:
        """
        Creates a new TabletopSystem instance.

        Args:
            **kwargs: Additional fields for the TabletopSystem

        Returns:
            TabletopSystem.
        """
        defaults = {
            "name": f"System {secrets.token_hex(12)}",
            "description": f"System {secrets.token_hex(20)}",
            "short_name": f"Sys {secrets.token_hex(6)}",
        }

        defaults.update(kwargs)

        return TabletopSystem.objects.create(**defaults)
