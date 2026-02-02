from django.urls import path

from .views import (
    CampaignCreateView,
    CampaignDetailView,
    CampaignUpdateView,
    JoinedCampaignListView,
    ManagedCampaignListView,
    PlayerCharacterCreateView,
    PlayerCharacterDetailView,
    PlayerCharacterListView,
    PlayerCharacterUpdateView,
    SplashView,
)

urlpatterns = [
    path("", SplashView.as_view(), name="splash"),
    # Campaign URLs
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
    # Character URLs
    path("characters/", PlayerCharacterListView.as_view(), name="character_list"),
    path(
        "character/new/",
        PlayerCharacterCreateView.as_view(),
        name="character_create",
    ),
    path(
        "character/<uuid:pk>/",
        PlayerCharacterDetailView.as_view(),
        name="character_detail",
    ),
    path(
        "character/<uuid:pk>/edit/",
        PlayerCharacterUpdateView.as_view(),
        name="character_edit",
    ),
]
