from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from dunbud.forms.journal import JournalEntryForm
from dunbud.models.journal import JournalEntry


class JournalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Allows a user to edit an existing journal entry.
    """

    model = JournalEntry
    form_class = JournalEntryForm
    template_name = "journal/journal_form.html"
    pk_url_kwarg = "entry_id"

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["character"] = self.object.character
        return kwargs

    def test_func(self) -> bool:
        entry = self.get_object()
        return entry.character.user == self.request.user

    def get_success_url(self) -> str:
        return reverse_lazy(
            "journal_list",
            kwargs={"character_id": self.object.character.pk},
        )
