import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.http import Http404
from django.views.generic import DetailView

from dunbud.forms import HelpfulLinkForm, PartyFeedItemForm
from dunbud.models import Campaign

logger = logging.getLogger(__name__)


class CampaignDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View to display the details of a specific campaign.
    Restricted to the Dungeon Master and joined players.
    """

    model = Campaign
    template_name = "campaign/campaign_detail.html"
    context_object_name = "campaign"

    def get_queryset(self) -> QuerySet[Campaign]:
        """
        Optimize database queries by pre-fetching related objects.
        """
        return (
            super()
            .get_queryset()
            .select_related("dungeon_master", "system")
            .prefetch_related(
                "players",
                "player_characters",
                "helpful_links",
                "sessions__attendees",
            )
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add list of players with their active character for this campaign.
        Also adds management forms for the Dungeon Master.
        """
        context = super().get_context_data(**kwargs)
        campaign = self.object  # type: ignore[attr-defined]

        if self.request.user == self.object.dungeon_master:
            # Fetch the most recent active invitation if it exists
            context["active_invite"] = self.object.invitations.filter(
                is_active=True,
            ).first()
            if "link_form" not in kwargs:
                context["link_form"] = HelpfulLinkForm()
            if "announcement_form" not in kwargs:
                context["announcement_form"] = PartyFeedItemForm()

        # Map user_id to their character in this campaign
        character_map = {
            char.user_id: char for char in campaign.player_characters.all()
        }

        # Annotate players with their character for this campaign
        players_with_data = []
        for player in campaign.players.all():
            player.campaign_character = character_map.get(player.pk)
            players_with_data.append(player)

        context["players_with_data"] = players_with_data
        return context

    def test_func(self) -> bool:
        """
        Checks if the current user is a member of the campaign (DM or Player).
        """
        try:
            campaign = self.get_object()
        except Http404:
            return True

        user = self.request.user  # type: ignore[misc]

        if campaign.dungeon_master == user or user in campaign.players.all():
            return True

        # Log unauthorized access attempts to existing campaigns.
        logger.warning(
            "Unauthorized access attempt to campaign %s by user %s",
            campaign.pk,
            user,
        )
        return False
