# dunbud/urls.py

from django.urls import path

from .views import (
    CampaignCreateView,
    JoinedCampaignListView,
    ManagedCampaignListView,
    SplashView,
)

urlpatterns = [
    path("", SplashView.as_view(), name="splash"),
    path("campaign/new/", CampaignCreateView.as_view(), name="campaign_create"),
    path(
        "campaigns/managed/",
        ManagedCampaignListView.as_view(),
        name="campaign_managed",
    ),
    path(
        "campaigns/joined/",
        JoinedCampaignListView.as_view(),
        name="campaign_joined",
    ),
]
