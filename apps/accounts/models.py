from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class UserSettings(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="settings",
    )

    classroom_notifications = models.BooleanField(
        default=True
    )

    assignment_notifications = models.BooleanField(
        default=True
    )

    quiz_notifications = models.BooleanField(
        default=True
    )

    alec_companion = models.BooleanField(
        default=True
    )

    alec_insights = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.user.username}'s settings"