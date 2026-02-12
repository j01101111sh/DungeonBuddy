from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from dunbud.models.journal import JournalEntry
from dunbud.models.player_character import PlayerCharacter


class JournalListView(LoginRequiredMixin, ListView):
    """
    Displays a list of journal entries for a specific character.
    """

    model = JournalEntry
    template_name = "journal/journal_list.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self) -> QuerySet[JournalEntry]:
        self.character = get_object_or_404(
            PlayerCharacter,
            pk=self.kwargs["character_id"],
        )
        return JournalEntry.objects.filter(character=self.character)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["character"] = self.character
        # Check if current user is the owner to show add/edit buttons
        context["is_owner"] = self.character.user == self.request.user
        return context
