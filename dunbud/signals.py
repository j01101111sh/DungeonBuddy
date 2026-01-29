import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Model
from django.db.models.signals import m2m_changed, pre_save
from django.dispatch import receiver

from dunbud.models import Campaign, PartyFeedItem

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
        old_instance = Campaign.objects.get(pk=instance.pk)
    except Campaign.DoesNotExist:
        # Should not happen in pre_save for an existing object, but safety first
        return

    # Check for Description Change
    if instance.description != old_instance.description:
        PartyFeedItem.objects.create(
            campaign=instance,
            message="The campaign description has been updated.",
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
        )
        logger.info("Feed item created: Video link %s for %s", action, instance.pk)


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
            )
            logger.info(
                "Feed item created: Player %s removed from %s",
                user.username,
                instance.pk,
            )
