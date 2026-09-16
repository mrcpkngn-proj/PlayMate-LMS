from django.conf import settings
from django.db import models

from apps.classroom.models import Classroom


class Notification(models.Model):

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    classroom = models.ForeignKey(
        "classroom.Classroom",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    title = models.CharField(
        max_length=150,
    )

    message = models.TextField()

    url = models.CharField(
        max_length=255,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = [
            "-created_at",
        ]

    def __str__(self):

        return self.title