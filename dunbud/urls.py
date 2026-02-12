from django.urls import path

from .views import (
    CampaignAnnouncementCreateView,
    CampaignCreateView,
    CampaignDetailView,
    CampaignInvitationCreateView,
    CampaignJoinView,
    CampaignUpdateView,
    HelpfulLinkCreateView,
    HelpfulLinkDeleteView,
    JoinedCampaignListView,
    JournalCreateView,
    JournalDeleteView,
    JournalListView,
    JournalUpdateView,
    ManagedCampaignListView,
    PlayerCharacterCreateView,
    PlayerCharacterDetailView,
    PlayerCharacterListView,
    PlayerCharacterUpdateView,
    SessionCreateView,
    SessionDetailView,
    SessionToggleAttendanceView,
    SessionUpdateView,
    SplashView,
)

urlpatterns = [
    path("", SplashView.as_view(), name="splash"),
    path("campaigns/new/", CampaignCreateView.as_view(), name="campaign_create"),
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
        "campaigns/<slug:slug>/",
        CampaignDetailView.as_view(),
        name="campaign_detail",
    ),
    path(
        "campaigns/<slug:slug>/edit/",
        CampaignUpdateView.as_view(),
        name="campaign_edit",
    ),
    path(
        "campaigns/<slug:slug>/invite/create/",
        CampaignInvitationCreateView.as_view(),
        name="campaign_invite_create",
    ),
    path(
        "invites/<str:token>/",
        CampaignJoinView.as_view(),
        name="campaign_join",
    ),
    # Feed URLs
    path(
        "campaigns/<slug:slug>/announcement/create/",
        CampaignAnnouncementCreateView.as_view(),
        name="campaign_announcement_create",
    ),
    # Link URLs
    path(
        "campaigns/<slug:slug>/links/add/",
        HelpfulLinkCreateView.as_view(),
        name="helpful_link_add",
    ),
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
    # Session URLs
    path(
        "campaigns/<slug:campaign_slug>/sessions/propose/",
        SessionCreateView.as_view(),
        name="session_propose",
    ),
    path(
        "sessions/<int:pk>/attendance/",
        SessionToggleAttendanceView.as_view(),
        name="session_toggle_attendance",
    ),
    path(
        "campaigns/<slug:campaign_slug>/sessions/<int:session_number>/",
        SessionDetailView.as_view(),
        name="session_detail",
    ),
    path(
        "campaigns/<slug:campaign_slug>/sessions/<int:session_number>/edit/",
        SessionUpdateView.as_view(),
        name="session_edit",
    ),
    # Journal URLs
    path(
        "character/<uuid:character_id>/journal/",
        JournalListView.as_view(),
        name="journal_list",
    ),
    path(
        "character/<uuid:character_id>/journal/new/",
        JournalCreateView.as_view(),
        name="journal_create",
    ),
    path(
        "journal/<uuid:entry_id>/edit/",
        JournalUpdateView.as_view(),
        name="journal_update",
    ),
    path(
        "journal/<uuid:entry_id>/delete/",
        JournalDeleteView.as_view(),
        name="journal_delete",
    ),
]
