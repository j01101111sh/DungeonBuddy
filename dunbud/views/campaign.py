import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DeleteView, View

from dunbud.forms import PartyFeedItemForm
from dunbud.models import Campaign, HelpfulLink, PartyFeedItem

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
