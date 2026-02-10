import pytest

from config.tests.factories import UserFactory
from dunbud.tests.factories import CampaignFactory, SessionFactory


@pytest.fixture
def user_factory():
    """Fixture for the UserFactory."""

    def factory(*args, **kwargs):
        return UserFactory.create(*args, **kwargs)

    return factory


@pytest.fixture
def campaign_factory(db):
    """Fixture for the CampaignFactory."""

    def factory(*args, **kwargs):
        return CampaignFactory.create(*args, **kwargs)

    return factory


@pytest.fixture
def session_factory(db):
    """Fixture for the SessionFactory."""

    def factory(*args, **kwargs):
        return SessionFactory.create(*args, **kwargs)

    return factory
