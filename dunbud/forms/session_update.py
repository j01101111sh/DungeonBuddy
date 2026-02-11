from django import forms

from dunbud.models import Session


class SessionUpdateForm(forms.ModelForm):
    """Form for updating an existing session, including notes."""

    class Meta:
        model = Session
        fields = ["proposed_date", "duration", "notes"]
        widgets = {
            "proposed_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
        }
