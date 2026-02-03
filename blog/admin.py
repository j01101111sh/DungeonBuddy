from typing import Any

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models
from django.http import HttpRequest

from blog.models import Post

User = get_user_model()


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Admin configuration for managing blog posts.
    """

    list_display = ("title", "author", "created_at", "is_published")
    list_filter = ("is_published", "created_at", "author")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"

    def formfield_for_foreignkey(
        self,
        db_field: models.ForeignKey[Any],
        request: HttpRequest,
        **kwargs: Any,
    ) -> Any:
        """
        Overrides the default form field for foreign keys.
        Specifically restricts the 'author' field to only show staff members.
        """
        if db_field.name == "author":
            kwargs["queryset"] = User.objects.filter(is_staff=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
