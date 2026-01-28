from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def ready(self) -> None:
        """
        Import signals when the app is ready.
        """
        import users.signals  # noqa: F401
