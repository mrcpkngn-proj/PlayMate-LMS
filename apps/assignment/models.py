from django.db import models
from django.conf import settings
from apps.classroom.models import Classwork

# Create your models here.
class Assignment(models.Model):

    classwork = models.OneToOneField(
        Classwork,
        on_delete=models.CASCADE,
        related_name="assignment",
    )

    points = models.PositiveIntegerField(default=100)

    instructions = models.TextField()

    def __str__(self):
        return self.classwork.title


class AssignmentAttachment(models.Model):

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    file = models.FileField(
        upload_to="assignment_files/",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.file.name


class Submission(models.Model):

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )

    submission_file = models.FileField(
        upload_to="assignment_submissions/",
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    feedback = models.TextField(
        blank=True,
    )

    is_returned = models.BooleanField(
        default=False,
    )

    class Meta:
        unique_together = (
            "assignment",
            "student",
        )

    def __str__(self):
        return f"{self.student.username} - {self.assignment.classwork.title}"