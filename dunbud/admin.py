from django.contrib import admin

from dunbud.models import Campaign, PlayerCharacter, TabletopSystem


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "dungeon_master", "created_at", "updated_at"]
    search_fields = ["name", "description", "dungeon_master__username"]
    list_filter = ["created_at", "updated_at"]
    filter_horizontal = ["players"]
    date_hierarchy = "created_at"


@admin.register(PlayerCharacter)
class PlayerCharacterAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "campaign", "level", "character_class"]
    search_fields = ["name", "user__username", "campaign__name"]
    list_filter = ["created_at", "level"]


@admin.register(TabletopSystem)
class TabletopSystemAdmin(admin.ModelAdmin):
    """
    Admin configuration for the TabletopSystem model.
    """

    list_display = ("name", "short_name", "description")
    search_fields = ("name",)
