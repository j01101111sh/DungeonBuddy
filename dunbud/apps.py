from django.apps import AppConfig


class DunbudConfig(AppConfig):
    name = "dunbud"

    def ready(self) -> None:
        """
        Import signals when the app is ready.
        """
        import dunbud.signals  # noqa: F401
