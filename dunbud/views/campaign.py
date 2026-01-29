import logging

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.forms.models import BaseModelForm
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from dunbud.models import Campaign

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
            .prefetch_related("players")
        )

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
        "vtt_link",
        "video_link",
        "players",  # Allow editing players to trigger player feed items
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
