from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
import random
import string
import os


def classroom_cover_path(instance, filename):
    extension = filename.split(".")[-1]

    if instance.pk:
        return f"classroom_covers/classroom_{instance.pk}/cover.{extension}"

    return os.path.join(
        "classroom_covers",
        "temp",
        filename,
    )

def generate_class_code():
    """
    Generates a unique 6-character classroom code.
    Example: A8F3QK
    """
    while True:
        code = "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=6
            )
        )

        if not Classroom.objects.filter(class_code=code).exists():
            return code


class Classroom(models.Model):

    name = models.CharField(
        max_length=150
    )

    description = models.TextField(
        blank=True
    )

    section = models.CharField(
        max_length=100,
        blank=True,
    )

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_classrooms",
    )

    class_code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_class_code,
        editable=False,
    )

    cover_image = models.ImageField(
        upload_to=classroom_cover_path,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class ClassroomMember(models.Model):

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="members",
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="joined_classrooms",
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            "classroom",
            "student",
        )

    def __str__(self):
        return f"{self.student.username} - {self.classroom.name}"



class Classwork(models.Model):

    TYPE_CHOICES = [
        ("assignment", "Assignment"),
        ("quiz", "Quiz"),
    ]

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="classwork_items",
    )

    title = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    work_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
    )

    due_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


class StreamPost(models.Model):

    POST_TYPES = [
        ("announcement", "Announcement"),
        ("assignment", "Assignment"),
        ("quiz", "Quiz"),
    ]

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="stream_posts",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPES,
    )

    message = models.TextField(
        blank=True,
    )

    assignment = models.ForeignKey(
        "assignment.Assignment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    quiz = models.ForeignKey(
        "quiz.Quiz",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = ["-created_at"]

    def __str__(self):

        return f"{self.classroom.name} - {self.post_type}"