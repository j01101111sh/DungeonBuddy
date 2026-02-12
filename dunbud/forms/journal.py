from typing import Any

from django import forms

from dunbud.models.journal import JournalEntry
from dunbud.models.player_character import PlayerCharacter
from dunbud.models.session import Session


class JournalEntryForm(forms.ModelForm):
    """
    Form for creating and updating journal entries.
    Filters the session dropdown to only show sessions from the character's campaign.
    """

    class Meta:
        model = JournalEntry
        fields = ["title", "session", "content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 10}),
        }

    def __init__(self, *args: Any, character: PlayerCharacter, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.character = character

        # Filter sessions to the character's campaign
        if self.character.campaign:
            self.fields["session"].queryset = Session.objects.filter(
                campaign=self.character.campaign,
            ).order_by("-session_number")
        else:
            # If character has no campaign, they cannot link to a session
            self.fields["session"].queryset = Session.objects.none()
            self.fields["session"].widget = forms.HiddenInput()

    def save(self, commit: bool = True) -> JournalEntry:
        entry = super().save(commit=False)
        entry.character = self.character
        if commit:
            entry.save()
        return entry
