import logging
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DeleteView, View

from dunbud.forms import HelpfulLinkForm, PartyFeedItemForm
from dunbud.models import Campaign, CampaignInvitation, HelpfulLink, PartyFeedItem

logger = logging.getLogger(__name__)


class CampaignInvitationCreateView(LoginRequiredMixin, View):
    """
    View to generate a new invitation link for a campaign.
    Only accessible by the Dungeon Master of the campaign.
    """

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        """
        Handle POST request to create a new invitation.
        """
        campaign = get_object_or_404(Campaign, pk=pk)

        # Permission check: Only DM can create invites
        if campaign.dungeon_master != request.user:
            logger.warning(
                "Unauthorized invite creation attempt by user %s for campaign %s",
                request.user.id,
                campaign.id,
            )
            messages.error(
                request,
                "Only the Dungeon Master can generate invitation links.",
            )
            return redirect("campaign_detail", pk=pk)

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
                    campaign.id,
                    request.user,
                )
                messages.success(request, "Invitation link generated.")
            else:
                logger.info(
                    "Retrieved existing invitation %s for campaign %s",
                    invite.id,
                    campaign.id,
                )
                messages.info(request, "Existing active invitation retrieved.")

        return redirect("campaign_detail", pk=pk)


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
            return redirect("campaign_detail", pk=campaign.pk)

        # 2. Check if already a player
        if request.user.pk and campaign.players.filter(pk=request.user.pk).exists():
            messages.info(request, "You are already a player in this campaign.")
            return redirect("campaign_detail", pk=campaign.pk)

        # 3. Check for player limit
        if campaign.players.count() >= campaign.max_players:
            logger.warning(
                "User %s attempted to join full campaign %s (Limit: %s)",
                request.user.id,
                campaign.id,
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
                campaign.id,
                invite.id,
            )
            messages.success(request, f"You have successfully joined {campaign.name}!")
        except Exception as e:
            logger.error(
                "Error adding user %s to campaign %s: %s",
                request.user.id,
                campaign.id,
                e,
            )
            messages.error(request, "An error occurred while joining the campaign.")

        return redirect("campaign_detail", pk=campaign.pk)


class HelpfulLinkCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to create a new helpful link via AJAX.
    """

    model = HelpfulLink
    form_class = HelpfulLinkForm

    def test_func(self) -> bool:
        self.campaign = get_object_or_404(Campaign, pk=self.kwargs["pk"])
        return bool(self.campaign.dungeon_master == self.request.user)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.form_class(request.POST)
        form.instance.campaign = self.campaign

        if form.is_valid():
            link = form.save()
            data = {
                "pk": link.pk,
                "name": link.name,
                "url": link.url,
                "delete_url": reverse("helpful_link_delete", kwargs={"pk": link.pk}),
            }
            return JsonResponse(data, status=201)
        return JsonResponse({"errors": form.errors}, status=400)


class HelpfulLinkDeleteView(LoginRequiredMixin, DeleteView):
    """
    View to delete a helpful link via AJAX.
    Restricted to the Dungeon Master of the campaign.
    """

    model = HelpfulLink

    def get_queryset(self) -> QuerySet:
        """
        Only allow the DM to delete links from their own campaign.
        """
        return super().get_queryset().filter(campaign__dungeon_master=self.request.user)

    def get_success_url(self) -> str:
        # Prevent redirection
        return ""

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Log the deletion and return a JSON response.
        """
        logger.info(
            "Deleted helpful link %s by user %s",
            self.object.pk,
            self.request.user,
        )
        super().form_valid(form)
        return JsonResponse({"message": "Link deleted successfully."})


class CampaignAnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to post a new announcement to the campaign feed.
    Restricted to the Dungeon Master.
    """

    def test_func(self) -> bool:
        """
        Only the Dungeon Master can post announcements.
        """
        self.campaign = get_object_or_404(Campaign, pk=self.kwargs["pk"])
        return bool(self.campaign.dungeon_master == self.request.user)

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        """
        Handle POST request to create a new announcement.
        """
        form = PartyFeedItemForm(request.POST)

        if form.is_valid():
            feed_item = form.save(commit=False)
            feed_item.campaign = self.campaign
            feed_item.category = PartyFeedItem.Category.ANNOUNCEMENT
            feed_item.save()

            logger.info(
                "Announcement posted to campaign %s by user %s",
                self.campaign.id,
                request.user,
            )
            messages.success(request, "Announcement posted successfully.")
        else:
            messages.error(request, "Failed to post announcement.")

        return redirect("campaign_detail", pk=pk)
