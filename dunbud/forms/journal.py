from typing import Any, cast

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

        session_field = cast(forms.ModelChoiceField, self.fields["session"])

        # Filter sessions to the character's campaign
        if self.character.campaign:
            session_field.queryset = Session.objects.filter(
                campaign=self.character.campaign,
            ).order_by("-session_number")
        else:
            # If character has no campaign, they cannot link to a session
            session_field.queryset = Session.objects.none()
            session_field.widget = forms.HiddenInput()

    def save(self, commit: bool = True) -> JournalEntry:
        entry: JournalEntry = super().save(commit=False)
        entry.character = self.character
        if commit:
            entry.save()
        return entry
