from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User = settings.AUTH_USER_MODEL


class Subscription(models.Model):

    user = models.ForeignKey(
        User, related_name='subscriptions', on_delete=models.CASCADE)

    author = models.ForeignKey(
        User, related_name='subscribers', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'author')


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} Profile"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
