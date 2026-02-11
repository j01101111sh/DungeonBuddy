from django import forms

from dunbud.models import Session


class SessionForm(forms.ModelForm):
    """Form for creating a new session."""

    class Meta:
        model = Session
        fields = ["proposed_date", "duration"]
        widgets = {
            "proposed_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
