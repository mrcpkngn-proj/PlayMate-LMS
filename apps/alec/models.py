from django.conf import settings
from django.db import models


class AlecMemorySnapshot(models.Model):

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alec_memory_snapshots",
    )

    classroom = models.ForeignKey(
        "classroom.Classroom",
        on_delete=models.CASCADE,
        related_name="alec_memory_snapshots",
    )

    overall_average = models.FloatField(default=0)

    quiz_average = models.FloatField(default=0)

    assignment_average = models.FloatField(default=0)

    completed_quizzes = models.PositiveIntegerField(default=0)

    graded_assignments = models.PositiveIntegerField(default=0)

    overdue_count = models.PositiveIntegerField(default=0)

    total_task_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"ALEC memory - "
            f"{self.student.username} - "
            f"{self.classroom.name}"
        )


class AlecMemoryEvent(models.Model):

    EVENT_TYPES = [
        ("quiz_completed", "Quiz Completed"),
        ("assignment_submitted", "Assignment Submitted"),
        ("grade_changed", "Grade Changed"),
        ("task_overdue", "Task Became Overdue"),
        ("classroom_revisited", "Classroom Revisited"),
        ("performance_improved", "Performance Improved"),
        ("performance_declined", "Performance Declined"),
        ("quiz_performance_changed", "Quiz Performance Changed"),
        ("assignment_performance_changed", "Assignment Performance Changed"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alec_memory_events",
    )

    classroom = models.ForeignKey(
        "classroom.Classroom",
        on_delete=models.CASCADE,
        related_name="alec_memory_events",
    )

    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
    )

    title = models.CharField(
        max_length=255,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    acknowledged = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.student.username} - "
            f"{self.event_type} - "
            f"{self.title}"
        )