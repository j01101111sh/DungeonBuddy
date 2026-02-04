from django.urls import path

from .views import (
    CampaignCreateView,
    CampaignDetailView,
    CampaignInvitationCreateView,
    CampaignJoinView,
    CampaignUpdateView,
    HelpfulLinkDeleteView,
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
    path(
        "campaigns/<uuid:pk>/invite/create/",
        CampaignInvitationCreateView.as_view(),
        name="campaign_invite_create",
    ),
    path(
        "invites/<str:token>/",
        CampaignJoinView.as_view(),
        name="campaign_join",
    ),
    # Link URLs
    path(
        "links/<int:pk>/delete/",
        HelpfulLinkDeleteView.as_view(),
        name="helpful_link_delete",
    ),
    # Character URLs
    path("characters/", PlayerCharacterListView.as_view(), name="character_list"),
    path(
        "characters/new/",
        PlayerCharacterCreateView.as_view(),
        name="character_create",
    ),
    path(
        "characters/<uuid:pk>/",
        PlayerCharacterDetailView.as_view(),
        name="character_detail",
    ),
    path(
        "characters/<uuid:pk>/edit/",
        PlayerCharacterUpdateView.as_view(),
        name="character_edit",
    ),
]
