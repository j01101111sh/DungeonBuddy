from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView

from dunbud.forms.journal import JournalEntryForm
from dunbud.models.journal import JournalEntry
from dunbud.models.player_character import PlayerCharacter


class JournalCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Allows a user to write a new journal entry for their character.
    """

    model = JournalEntry
    form_class = JournalEntryForm
    template_name = "journal/journal_form.html"

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        self.character = get_object_or_404(
            PlayerCharacter,
            pk=self.kwargs["character_id"],
        )
        kwargs["character"] = self.character
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["character"] = self.character
        return context

    def test_func(self) -> bool:
        # Only the character's owner can write a journal
        character = get_object_or_404(PlayerCharacter, pk=self.kwargs["character_id"])
        return character.user == self.request.user

    def get_success_url(self) -> str:
        return reverse_lazy(
            "journal_list",
            kwargs={"character_id": self.character.pk},
        )
