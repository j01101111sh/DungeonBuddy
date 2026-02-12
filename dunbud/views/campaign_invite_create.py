import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View

from dunbud.models import Campaign, CampaignInvitation

logger = logging.getLogger(__name__)


class CampaignInvitationCreateView(LoginRequiredMixin, View):
    """
    View to generate a new invitation link for a campaign.
    Only accessible by the Dungeon Master of the campaign.
    """

    def post(self, request: HttpRequest, slug: str) -> HttpResponse:
        """
        Handle POST request to create a new invitation.
        """
        campaign = get_object_or_404(Campaign, slug=slug)

        # Permission check: Only DM can create invites
        if campaign.dungeon_master != request.user:
            logger.warning(
                "Unauthorized invite creation attempt by user %s for campaign %s",
                request.user.id,
                campaign.slug,
            )
            messages.error(
                request,
                "Only the Dungeon Master can generate invitation links.",
            )
            return redirect("campaign_detail", slug=slug)

        # Invalidate old invites (optional logic, keeping it clean for now by just creating a new one)
        # or get existing active one to ensure idempotency if desired.
        # Here we create a new one as requested by the 'Generate' action.

        with transaction.atomic():
            # Optional: Deactivate old invites to ensure only one valid link at a time
            # campaign.invitations.update(is_active=False)

            invite, created = CampaignInvitation.objects.get_or_create(
                campaign=campaign,
                is_active=True,
            )

            if created:
                logger.info(
                    "Created new invitation %s for campaign %s by %s",
                    invite.id,
                    campaign.slug,
                    request.user,
                )
                messages.success(request, "Invitation link generated.")
            else:
                logger.info(
                    "Retrieved existing invitation %s for campaign %s",
                    invite.id,
                    campaign.slug,
                )
                messages.info(request, "Existing active invitation retrieved.")

        return redirect("campaign_detail", slug=slug)
