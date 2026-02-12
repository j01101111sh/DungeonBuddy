from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import DeleteView

from dunbud.models.journal import JournalEntry


class JournalDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Allows a user to delete a journal entry.
    """

    model = JournalEntry
    template_name = "journal/journal_confirm_delete.html"
    pk_url_kwarg = "entry_id"

    def test_func(self) -> bool:
        entry = self.get_object()
        return entry.character.user == self.request.user

    def get_success_url(self) -> str:
        return reverse_lazy(
            "journal_list",
            kwargs={"character_id": self.object.character.pk},
        )
