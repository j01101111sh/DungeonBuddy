from django.urls import path

from .views import CampaignCreateView, SplashView

urlpatterns = [
    path("", SplashView.as_view(), name="splash"),
    path("campaign/new/", CampaignCreateView.as_view(), name="campaign_create"),
]
