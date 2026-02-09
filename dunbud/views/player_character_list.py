import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.views.generic import ListView

from dunbud.models import PlayerCharacter

logger = logging.getLogger(__name__)


class PlayerCharacterListView(LoginRequiredMixin, ListView):
    """
    View to list characters belonging to the current user.
    """

    model = PlayerCharacter
    template_name = "character/character_list.html"
    context_object_name = "characters"

    def get_queryset(self) -> QuerySet[PlayerCharacter]:
        """
        Returns characters owned by the logged-in user.
        """
        if not self.request.user.is_authenticated:
            return PlayerCharacter.objects.none()
        return PlayerCharacter.objects.filter(user=self.request.user)
