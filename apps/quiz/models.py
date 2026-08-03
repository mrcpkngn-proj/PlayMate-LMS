from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.classroom.models import Classroom, Classwork


class Quiz(models.Model):

    classwork = models.OneToOneField(
        Classwork,
        on_delete=models.CASCADE,
        related_name="quiz",
    )

    duration = models.PositiveIntegerField(
        help_text="Time limit in minutes."
    )

    max_attempts = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of times a student can attempt this quiz."
    )

    shuffle_questions = models.BooleanField(default=False)

    shuffle_choices = models.BooleanField(default=False)

    DISPLAY_CHOICES = [
        ("per_question", "One Question Per Page"),
        ("single_page", "All Questions on One Page"),
    ]

    display_mode = models.CharField(
        max_length=20,
        choices=DISPLAY_CHOICES,
        default="per_question",
    )

    use_question_timer = models.BooleanField(
        default=False,
        verbose_name="Enable Per-Question Timer"
    )

    def __str__(self):
        return self.classwork.title


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.TextField()
    points = models.PositiveIntegerField(default=1)
    answer_type = models.CharField(
        max_length=10,
        choices=[
            ("single", "Single Answer"),
            ("multiple", "Multiple Answers"),
        ],
        default="single",
    )
    duration = models.IntegerField(default=30)  # seconds allowed for this question

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Attempt(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_completed = models.BooleanField(default=False)

    question_order = models.JSONField(
        default=list,
        blank=True,
    )

    choice_order = models.JSONField(
        default=dict,
        blank=True,
    )

    current_question = models.PositiveIntegerField(
        default=0
    )

    def __str__(self):
        return f"{self.student} - {self.quiz}"

    def is_active(self):
        """Check if attempt is still valid based on quiz timer."""
        end_time = self.started_at + timedelta(minutes=self.quiz.duration)
        return not self.is_completed and timezone.now() < end_time


class Answer(models.Model):
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Answer for {self.question}"