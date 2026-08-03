from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.assignment.models import Assignment
from apps.quiz.models import Quiz
from .models import StreamPost


@receiver(post_save, sender=Assignment)
def create_assignment_stream_post(sender, instance, created, **kwargs):

    if not created:
        return

    StreamPost.objects.create(

        classroom=instance.classwork.classroom,

        author=instance.classwork.created_by,

        post_type="assignment",

        assignment=instance,

    )


@receiver(post_save, sender=Quiz)
def create_quiz_stream_post(sender, instance, created, **kwargs):

    if not created:
        return

    StreamPost.objects.create(

        classroom=instance.classwork.classroom,

        author=instance.classwork.created_by,

        post_type="quiz",

        quiz=instance,

    )