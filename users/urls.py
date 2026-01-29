from django.contrib.auth import urls as auth_urls
from django.urls import include, path

from users.views import SignUpView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    # Include default auth urls (login, logout, password_change, etc.)
    path("", include(auth_urls)),
]
