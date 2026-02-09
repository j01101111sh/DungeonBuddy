import logging

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView

from dunbud.models import PlayerCharacter

logger = logging.getLogger(__name__)


class PlayerCharacterDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View to display character details.
    Visible to the owner and members (DM/Players) of the assigned campaign.
    """

    model = PlayerCharacter
    template_name = "character/character_detail.html"
    context_object_name = "character"

    def test_func(self) -> bool:
        """
        Check if the user is allowed to view the character.
        """
        character = self.get_object()
        user = self.request.user

        # Owner access
        if character.user == user:
            return True

        # Campaign members access
        if character.campaign:
            if character.campaign.dungeon_master == user:
                return True
            if user in character.campaign.players.all():
                return True

        return False
