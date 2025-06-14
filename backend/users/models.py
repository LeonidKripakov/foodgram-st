from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Subscription(models.Model):

    user = models.ForeignKey(
        User, related_name='subscriptions', on_delete=models.CASCADE)

    author = models.ForeignKey(
        User, related_name='subscribers', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'author')
