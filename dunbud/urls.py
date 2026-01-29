from django.urls import path

from .views import (
    CampaignCreateView,
    CampaignDetailView,
    CampaignUpdateView,
    JoinedCampaignListView,
    ManagedCampaignListView,
    SplashView,
)

urlpatterns = [
    path("", SplashView.as_view(), name="splash"),
    path("campaign/new/", CampaignCreateView.as_view(), name="campaign_create"),
    path(
        "campaign/<uuid:pk>/",
        CampaignDetailView.as_view(),
        name="campaign_detail",
    ),
    path(
        "campaign/<uuid:pk>/edit/",
        CampaignUpdateView.as_view(),
        name="campaign_edit",
    ),
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
