import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

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
    success_url = reverse_lazy("splash")

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
