import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from ..models import Session


@pytest.mark.django_db
def test_session_creation(user_factory, campaign_factory):
    """Test that a session can be created."""
    dm, _ = user_factory()
    campaign = campaign_factory(dungeon_master=dm)
    proposer = dm
    proposed_date = timezone.now()

    session = Session.objects.create(
        campaign=campaign,
        proposer=proposer,
        proposed_date=proposed_date,
        duration=3,
    )

    assert session.campaign == campaign
    assert session.proposer == proposer
    assert session.duration == 3
    assert str(session) == f"Session for {campaign.name} at {session.proposed_date}"


@pytest.mark.django_db
def test_session_propose_view(client, user_factory, campaign_factory):
    """Test the view for proposing a new session."""
    dm, _ = user_factory()
    campaign = campaign_factory(dungeon_master=dm)
    client.force_login(dm)

    url = reverse("session_propose", kwargs={"campaign_pk": campaign.pk})
    response = client.get(url)
    assert response.status_code == 200

    proposed_date = timezone.now() + datetime.timedelta(days=7)

    response = client.post(
        url,
        {
            "proposed_date": proposed_date.strftime("%Y-%m-%dT%H:%M"),
            "duration": 4,
        },
    )

    assert response.status_code == 302
    assert Session.objects.filter(campaign=campaign, duration=4).exists()


@pytest.mark.django_db
def test_toggle_attendance(client, user_factory, campaign_factory, session_factory):
    """Test toggling a player's attendance for a session."""
    dm, _ = user_factory()
    player, _ = user_factory()
    campaign = campaign_factory(dungeon_master=dm)
    campaign.players.add(player)
    session = session_factory(campaign=campaign, proposer=dm)

    client.force_login(player)

    url = reverse("session_toggle_attendance", kwargs={"pk": session.pk})

    # Add attendance
    response = client.post(url)
    assert response.status_code == 302
    session.refresh_from_db()
    assert player in session.attendees.all()

    # Remove attendance
    response = client.post(url)
    assert response.status_code == 302
    session.refresh_from_db()
    assert player not in session.attendees.all()
