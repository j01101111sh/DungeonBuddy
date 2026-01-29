from django.contrib.auth import urls as auth_urls
from django.urls import include, path

from users.views import SignUpView
from users.views.profiles import UserUpdateView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("profile/edit/", UserUpdateView.as_view(), name="profile_edit"),
    path("", include(auth_urls)),
]
