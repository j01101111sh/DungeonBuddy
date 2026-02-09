import logging

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import UpdateView

from dunbud.models import PlayerCharacter

logger = logging.getLogger(__name__)


class PlayerCharacterUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View to update an existing character.
    """

    model = PlayerCharacter
    fields = [
        "name",
        "race",
        "character_class",
        "level",
        "bio",
        "campaign",
        "character_sheet_link",
    ]
    template_name = "character/character_form.html"

    def test_func(self) -> bool:
        """
        Only the owner can edit the character.
        """
        character = self.get_object()
        return bool(character.user == self.request.user)

    def get_success_url(self) -> str:
        return reverse("character_detail", kwargs={"pk": self.object.pk})
