from django import forms

from dunbud.models import Session


class SessionUpdateForm(forms.ModelForm):
    """Form for updating an existing session, including notes and recap."""

    class Meta:
        model = Session
        fields = ["proposed_date", "duration", "notes", "recap"]
        widgets = {
            "proposed_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
            "recap": forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
        }
