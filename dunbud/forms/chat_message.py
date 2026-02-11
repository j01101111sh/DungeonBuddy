from django import forms

from dunbud.models import ChatMessage


class ChatMessageForm(forms.ModelForm):
    """
    Form for creating a new ChatMessage.
    """

    class Meta:
        model = ChatMessage
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Type your message here...",
                },
            ),
        }
