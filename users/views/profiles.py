from typing import Any

from django.contrib.auth import get_user_model
from django.views.generic import DetailView

User = get_user_model()


class UserDetailView(DetailView):
    model = User
    template_name = "users/user_detail.html"
    context_object_name = "profile_user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["reviews"] = self.object.review_set.select_related("movie").order_by(
            "-created_at",
        )
        return context
