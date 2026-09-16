from .models import Notification


def create_notification(
    recipient,
    title,
    message,
    url="",
    classroom=None,
):

    Notification.objects.create(

        recipient=recipient,

        title=title,

        classroom=classroom,

        message=message,

        url=url,

    )