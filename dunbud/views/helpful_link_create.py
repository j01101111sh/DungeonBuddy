import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import View

from dunbud.forms import HelpfulLinkForm
from dunbud.models import Campaign, HelpfulLink

logger = logging.getLogger(__name__)


class HelpfulLinkCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to create a new helpful link via AJAX.
    """

    model = HelpfulLink
    form_class = HelpfulLinkForm

    def test_func(self) -> bool:
        self.campaign = get_object_or_404(Campaign, slug=self.kwargs["slug"])
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
