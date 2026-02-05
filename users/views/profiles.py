from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView

from users.forms import CustomUserChangeForm

User = get_user_model()


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = "users/user_edit.html"
    success_url = reverse_lazy("profile_edit")

    def get_object(self, queryset: QuerySet[Any] | None = None) -> Any:
        # Override to return the current user, ignoring any URL parameters
        return self.request.user

    def form_valid(self, form: CustomUserChangeForm) -> HttpResponse:
        from django.contrib import messages

        messages.success(self.request, "Your profile has been updated successfully.")
        return super().form_valid(form)


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "users/user_detail.html"
