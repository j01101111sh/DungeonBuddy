from django import forms

from .models import HelpfulLink


class HelpfulLinkForm(forms.ModelForm):
    """
    A form for creating and editing helpful links.
    """

    class Meta:
        model = HelpfulLink
        fields = ["name", "url"]
