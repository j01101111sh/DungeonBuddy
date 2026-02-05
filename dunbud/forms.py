from django import forms
from django.utils.translation import gettext_lazy as _

from .models import HelpfulLink, PartyFeedItem


class HelpfulLinkForm(forms.ModelForm):
    """
    A form for creating and editing helpful links.
    """

    class Meta:
        model = HelpfulLink
        fields = ["name", "url"]

    def clean_url(self) -> str:
        url = self.cleaned_data["url"]
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        return str(url)


class PartyFeedItemForm(forms.ModelForm):
    """
    Form for creating a new party feed item (announcement).
    """

    class Meta:
        model = PartyFeedItem
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _(
                        "Post an announcement... (Markdown supported: **bold**, *italics*, [links](url))",
                    ),
                },
            ),
        }
