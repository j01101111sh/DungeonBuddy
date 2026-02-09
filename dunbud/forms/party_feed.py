from django import forms
from django.utils.translation import gettext_lazy as _

from dunbud.models import PartyFeedItem


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
