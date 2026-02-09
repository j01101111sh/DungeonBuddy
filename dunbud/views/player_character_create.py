import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import CreateView

from dunbud.models import PlayerCharacter

logger = logging.getLogger(__name__)


class PlayerCharacterCreateView(LoginRequiredMixin, CreateView):
    """
    View to create a new character.
    """

    model = PlayerCharacter
    fields = ["name", "race", "character_class", "level", "bio", "campaign"]
    template_name = "character/character_form.html"

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Sets the owner of the character to the current user.
        """
        # Ensure user is authenticated for type safety
        if not self.request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        if self.object:
            return reverse("character_detail", kwargs={"pk": self.object.pk})
        return reverse("character_list")
