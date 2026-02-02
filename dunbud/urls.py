from django.urls import path

from .views import (
    CampaignCreateView,
    CampaignDetailView,
    CampaignUpdateView,
    CharacterCreateView,
    CharacterDetailView,
    CharacterListView,
    CharacterUpdateView,
    JoinedCampaignListView,
    ManagedCampaignListView,
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
    path("characters/", CharacterListView.as_view(), name="character_list"),
    path("character/new/", CharacterCreateView.as_view(), name="character_create"),
    path(
        "character/<uuid:pk>/",
        CharacterDetailView.as_view(),
        name="character_detail",
    ),
    path(
        "character/<uuid:pk>/edit/",
        CharacterUpdateView.as_view(),
        name="character_edit",
    ),
]
