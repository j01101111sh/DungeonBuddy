from django.contrib import admin

from dunbud.models import Campaign, TabletopSystem


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "dungeon_master", "created_at", "updated_at"]
    search_fields = ["name", "description", "dungeon_master__username"]
    list_filter = ["created_at", "updated_at"]
    filter_horizontal = ["players"]
    date_hierarchy = "created_at"


@admin.register(TabletopSystem)
class TabletopSystemAdmin(admin.ModelAdmin):
    """
    Admin configuration for the TabletopSystem model.
    """

    list_display = ("name", "description")
    search_fields = ("name",)
