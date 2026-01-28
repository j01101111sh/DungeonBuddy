from django.urls import path

from .views import SplashView

urlpatterns = [
    path("", SplashView.as_view(), name="splash"),
]
