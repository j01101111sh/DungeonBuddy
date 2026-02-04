import logging
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import QuerySet
from django.forms.models import BaseModelForm
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from dunbud.forms import HelpfulLinkForm
from dunbud.models import HelpfulLink
from dunbud.models.campaign import Campaign, CampaignInvitation

logger = logging.getLogger(__name__)


class CampaignCreateView(LoginRequiredMixin, CreateView):
    """
    View to create a new campaign.
    The logged-in user is automatically assigned as the Dungeon Master.
    """

    model = Campaign
    fields = [
        "name",
        "description",
        "system",
        "max_players",
        "vtt_link",
        "video_link",
    ]
    template_name = "campaign/campaign_form.html"

    def get_success_url(self) -> str:
        """
        Redirects to the detail page of the created campaign.
        """
        if self.object:
            return reverse("campaign_detail", kwargs={"pk": self.object.pk})
        return reverse("splash")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Sets the current user as the dungeon master before saving.
        Logs the creation action.
        """
        # Ensure user is authenticated for type safety
        if not self.request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)

        form.instance.dungeon_master = self.request.user
        response = super().form_valid(form)

        if self.object:
            logger.info(
                "Campaign created via view: %s (ID: %s) by user %s",
                self.object.name,
                self.object.pk,
                self.request.user,
            )
        return response


class ManagedCampaignListView(LoginRequiredMixin, ListView):
    """
    View to list campaigns managed by the current user.
    """

    model = Campaign
    template_name = "campaign/managed_campaign_list.html"
    context_object_name = "campaigns"

    def get_queryset(self) -> QuerySet[Campaign]:
        """
        Returns the campaigns where the current user is the Dungeon Master.
        """
        if not self.request.user.is_authenticated:
            return Campaign.objects.none()

        return Campaign.objects.filter(dungeon_master=self.request.user)


class JoinedCampaignListView(LoginRequiredMixin, ListView):
    """
    View to list campaigns the current user has joined.
    """

    model = Campaign
    template_name = "campaign/joined_campaign_list.html"
    context_object_name = "campaigns"

    def get_queryset(self) -> QuerySet[Campaign]:
        """
        Returns the campaigns where the current user is a player.
        """
        if not self.request.user.is_authenticated:
            return Campaign.objects.none()

        return Campaign.objects.filter(players=self.request.user)


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
            .prefetch_related("players", "player_characters", "helpful_links")
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add list of players with their active character for this campaign.
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

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handles the POST request for adding a helpful link.
        """
        self.object = self.get_object()
        campaign = self.object
        if request.user != campaign.dungeon_master:
            messages.error(request, "You do not have permission to add links.")
            return self.get(request, *args, **kwargs)

        form = HelpfulLinkForm(request.POST)
        # Manually assign campaign to instance before validation
        form.instance.campaign = campaign
        if form.is_valid():
            form.save()
            messages.success(request, "Helpful link added successfully.")
            return redirect("campaign_detail", pk=campaign.pk)
        messages.error(request, "There was an error with the form.")
        kwargs["link_form"] = form
        return self.get(request, *args, **kwargs)

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


class CampaignUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View to edit an existing campaign.
    Restricted to the Dungeon Master.
    """

    model = Campaign
    fields = [
        "name",
        "description",
        "system",
        "max_players",
        "vtt_link",
        "video_link",
    ]
    template_name = "campaign/campaign_form.html"
    context_object_name = "campaign"

    def test_func(self) -> bool:
        """
        Only the Dungeon Master can edit the campaign.
        """
        campaign = self.get_object()
        return bool(campaign.dungeon_master == self.request.user)

    def get_success_url(self) -> str:
        return reverse("campaign_detail", kwargs={"pk": self.object.pk})


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


class HelpfulLinkDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View to delete a helpful link.
    Restricted to the Dungeon Master of the campaign.
    """

    model = HelpfulLink
    template_name = "campaign/helpful_link_confirm_delete.html"

    def get_success_url(self) -> str:
        """
        Redirects to the campaign detail page after deletion.
        """
        return reverse("campaign_detail", kwargs={"pk": self.object.campaign.pk})

    def test_func(self) -> bool:
        """
        Only the Dungeon Master can delete a helpful link.
        """
        link = self.get_object()
        return bool(link.campaign.dungeon_master == self.request.user)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.success(self.request, "Helpful link deleted successfully.")
        return super().form_valid(form)
