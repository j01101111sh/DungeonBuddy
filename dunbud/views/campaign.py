import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView

from dunbud.models import Campaign

logger = logging.getLogger(__name__)


class CampaignCreateView(LoginRequiredMixin, CreateView):
    """
    View to create a new campaign.
    The logged-in user is automatically assigned as the Dungeon Master.
    """

    model = Campaign
    fields = ["name", "description"]
    template_name = "campaign/campaign_form.html"
    success_url = reverse_lazy("splash")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Sets the current user as the dungeon master before saving.
        Logs the creation action.
        """
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
