import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView

from users.forms import CustomUserCreationForm

User = get_user_model()
logger = logging.getLogger(__name__)


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")  # Assuming 'login' URL will exist
    template_name = "registration/signup.html"

    def form_valid(self, form: CustomUserCreationForm) -> HttpResponse:
        response = super().form_valid(form)
        user = self.object

        if user and user.email:
            try:
                send_mail(
                    subject="Welcome to Dungeon Buddy!",
                    message=(
                        f"Hi {user.username},\n\n"
                        "Thanks for signing up for Dungeon Buddy! "
                        "We are excited to help you manage your campaigns."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                masked_email = user.email
                if "@" in user.email:
                    local, domain = user.email.rsplit("@", 1)
                    if len(local) > 2:
                        masked_email = (
                            f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"
                        )

                logger.info(
                    "Signup confirmation email sent to user: %s (%s)",
                    user.username,
                    masked_email,
                )
            except Exception:
                logger.exception(
                    "Failed to send signup confirmation email to user: %s",
                    user.username,
                )

        return response
