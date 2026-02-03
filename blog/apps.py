from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BlogConfig(AppConfig):
    """
    Configuration for the Blog application.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"
    verbose_name = _("Site Announcements")
