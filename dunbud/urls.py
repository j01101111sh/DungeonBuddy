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
    path("campaigns/new/", CampaignCreateView.as_view(), name="campaign_create"),
    path(
        "campaigns/<uuid:pk>/",
        CampaignDetailView.as_view(),
        name="campaign_detail",
    ),
    path(
        "campaigns/<uuid:pk>/edit/",
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
