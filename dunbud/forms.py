from django import forms

from .models import HelpfulLink


class HelpfulLinkForm(forms.ModelForm):
    """
    A form for creating and editing helpful links.
    """

    class Meta:
        model = HelpfulLink
        fields = ["name", "url"]

    def clean_url(self) -> str:
        """
        Automatically prepend 'https://' to the URL if no scheme is present.
        """
        url = self.cleaned_data["url"]
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        return str(url)
