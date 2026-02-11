from django.contrib import admin

from dunbud.models import (
    Campaign,
    CampaignInvitation,
    HelpfulLink,
    PlayerCharacter,
    TabletopSystem,
)
from dunbud.models.session import Session


class CampaignInvitationInline(admin.TabularInline):
    model = CampaignInvitation
    extra = 0
    readonly_fields = ("token", "created_at")


class HelpfulLinkInline(admin.TabularInline):
    model = HelpfulLink
    extra = 0


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "dungeon_master", "created_at", "updated_at"]
    search_fields = ["name", "description", "dungeon_master__username"]
    list_filter = ["created_at", "updated_at"]
    filter_horizontal = ["players"]
    date_hierarchy = "created_at"
    inlines = [CampaignInvitationInline, HelpfulLinkInline]


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


@admin.register(CampaignInvitation)
class CampaignInvitationAdmin(admin.ModelAdmin):
    list_display = ("campaign", "created_at", "is_active")
    list_filter = ("is_active", "created_at")
    search_fields = ("campaign__name",)
    readonly_fields = ("token",)


@admin.register(HelpfulLink)
class HelpfulLinkAdmin(admin.ModelAdmin):
    list_display = ["name", "url", "campaign"]
    search_fields = ["name", "url", "campaign__name"]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["campaign", "session_number", "proposed_date", "proposer"]
    search_fields = ["campaign__name", "proposer__username"]
    list_filter = ["campaign", "proposed_date"]
