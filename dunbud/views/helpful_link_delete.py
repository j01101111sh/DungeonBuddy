import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpResponse, JsonResponse
from django.views.generic import DeleteView

from dunbud.models import HelpfulLink

logger = logging.getLogger(__name__)


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
