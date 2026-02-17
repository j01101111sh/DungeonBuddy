import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Model
from django.db.models.signals import m2m_changed, pre_save
from django.dispatch import receiver

from dunbud.models import Campaign, PartyFeedItem, Session

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(pre_save, sender=Campaign)
def track_campaign_changes(
    sender: type[Campaign],
    instance: Campaign,
    **kwargs: Any,
) -> None:
    """
    Signal to track changes to Campaign fields (description, links)
    and create PartyFeedItems.
    """
    # If the instance is new (no primary key), it's a creation, not an update.
    if instance._state.adding:
        return

    try:
        old_instance = Campaign.objects.get(slug=instance.slug)
    except Campaign.DoesNotExist:
        # Should not happen in pre_save for an existing object, but safety first
        return

    # Check for Description Change
    if instance.description != old_instance.description:
        PartyFeedItem.objects.create(
            campaign=instance,
            message="The campaign description has been updated.",
            category=PartyFeedItem.Category.DATA_UPDATE,
        )
        logger.info("Feed item created: Description updated for %s", instance.pk)

    # Check for VTT Link Change
    if instance.vtt_link != old_instance.vtt_link:
        action = "added" if not old_instance.vtt_link else "updated"
        if not instance.vtt_link:
            action = "removed"

        PartyFeedItem.objects.create(
            campaign=instance,
            message=f"The Virtual Tabletop link was {action}.",
            category=PartyFeedItem.Category.DATA_UPDATE,
        )
        logger.info("Feed item created: VTT link %s for %s", action, instance.pk)

    # Check for Video Link Change
    if instance.video_link != old_instance.video_link:
        action = "added" if not old_instance.video_link else "updated"
        if not instance.video_link:
            action = "removed"

        PartyFeedItem.objects.create(
            campaign=instance,
            message=f"The Video Conference link was {action}.",
            category=PartyFeedItem.Category.DATA_UPDATE,
        )
        logger.info("Feed item created: Video link %s for %s", action, instance.pk)


@receiver(pre_save, sender=Session)
def track_session_recap_changes(
    sender: type[Session],
    instance: Session,
    **kwargs: Any,
) -> None:
    """
    Signal to track changes to Session recap and create PartyFeedItems.
    """
    # If the instance is new, we generally don't post a recap immediately
    if instance._state.adding:
        return

    try:
        old_instance = Session.objects.get(pk=instance.pk)
    except Session.DoesNotExist:
        return

    # Check for Recap Change
    # We only notify if the recap has content and is different from before.
    if instance.recap != old_instance.recap and instance.recap:
        PartyFeedItem.objects.create(
            campaign=instance.campaign,
            message=f"Session {instance.session_number} recap has been posted.",
            category=PartyFeedItem.Category.RECAP,
        )
        logger.info("Feed item created: Recap updated for Session %s", instance.pk)


@receiver(m2m_changed, sender=Campaign.players.through)
def track_player_changes(
    sender: Any,
    instance: Campaign,
    action: str,
    reverse: bool,
    model: type[Model],
    pk_set: set[Any],
    **kwargs: Any,
) -> None:
    """
    Signal to track players joining or leaving the campaign.
    """
    # We only care about forward relations (Campaign -> Players)
    if reverse:
        return

    if action == "post_add":
        users_added = User.objects.filter(pk__in=pk_set)
        for user in users_added:
            PartyFeedItem.objects.create(
                campaign=instance,
                message=f"{user.username} joined the party.",
                category=PartyFeedItem.Category.MEMBERSHIP,
            )
            logger.info(
                "Feed item created: Player %s added to %s",
                user.username,
                instance.pk,
            )

    elif action == "post_remove":
        users_removed = User.objects.filter(pk__in=pk_set)
        for user in users_removed:
            PartyFeedItem.objects.create(
                campaign=instance,
                message=f"{user.username} left the party.",
                category=PartyFeedItem.Category.MEMBERSHIP,
            )
            logger.info(
                "Feed item created: Player %s removed from %s",
                user.username,
                instance.pk,
            )
