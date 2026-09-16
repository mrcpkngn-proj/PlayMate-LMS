from .models import Notification


def notifications(request):

    if not request.user.is_authenticated:

        return {}

    unread = Notification.objects.filter(

        recipient=request.user,

        is_read=False,

    )

    return {

        "notification_count": unread.count(),

        "latest_notifications": unread[:20],

    }