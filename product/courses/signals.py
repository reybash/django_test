from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import assign_user_to_group
from users.models import Subscription


@receiver(post_save, sender=Subscription)
def post_save_subscription(sender, instance: Subscription, created, **kwargs):
    """
    Распределение нового студента в группу курса.

    """

    if created:
        assign_user_to_group(instance.user, instance.course)
