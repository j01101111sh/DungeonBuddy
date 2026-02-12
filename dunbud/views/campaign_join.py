import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View

from dunbud.models import CampaignInvitation

logger = logging.getLogger(__name__)


class CampaignJoinView(LoginRequiredMixin, View):
    """
    View to process a user clicking an invitation link.
    """

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        """
        Validate token and add user to campaign.
        """
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        invite = get_object_or_404(CampaignInvitation, token=token, is_active=True)
        campaign = invite.campaign

        # 1. Prevent DM from joining as a player
        if request.user == campaign.dungeon_master:
            messages.warning(request, "You are the Dungeon Master of this campaign.")
            return redirect("campaign_detail", slug=campaign.slug)

        # 2. Check if already a player
        if request.user.pk and campaign.players.filter(pk=request.user.pk).exists():
            messages.info(request, "You are already a player in this campaign.")
            return redirect("campaign_detail", slug=campaign.slug)

        # 3. Check for player limit
        if campaign.players.count() >= campaign.max_players:
            logger.warning(
                "User %s attempted to join full campaign %s (Limit: %s)",
                request.user.id,
                campaign.slug,
                campaign.max_players,
            )
            messages.error(request, "This campaign has reached its player limit.")
            # Redirect to 'joined' list (safe for non-members) instead of detail view (403 forbidden)
            return redirect("campaign_joined")

        # 4. Add to players
        try:
            campaign.players.add(request.user)
            logger.info(
                "User %s joined campaign %s via invite %s",
                request.user.id,
                campaign.slug,
                invite.id,
            )
            messages.success(request, f"You have successfully joined {campaign.name}!")
        except Exception as e:
            logger.error(
                "Error adding user %s to campaign %s: %s",
                request.user.id,
                campaign.slug,
                e,
            )
            messages.error(request, "An error occurred while joining the campaign.")

        return redirect("campaign_detail", slug=campaign.slug)
        return redirect("campaign_detail", slug=campaign.slug)
