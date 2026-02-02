from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    # This explicit type hint fixes the [no-any-return] error
    # by telling mypy that objects returns Post instances.
    class PostManager(models.Manager["Post"]):
        pass


class Post(models.Model):
    """
    Model representing a blog post or site announcement.
    """

    title = models.CharField(
        max_length=200,
        help_text=_("The title of the announcement."),
    )
    slug = models.SlugField(
        unique=True,
        help_text=_("URL-friendly version of the title."),
    )
    content = models.TextField(
        help_text=_("The body content of the announcement."),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_posts",
        help_text=_("The admin who created the post."),
    )
    is_published = models.BooleanField(
        default=False,
        help_text=_("Designates whether this post is visible to the public."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("The date and time when the post was created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("The date and time when the post was last updated."),
    )

    if TYPE_CHECKING:
        objects: PostManager

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Announcement")
        verbose_name_plural = _("Announcements")

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        """
        Returns the canonical URL for the post.
        """
        return reverse("blog:post_detail", kwargs={"slug": self.slug})
