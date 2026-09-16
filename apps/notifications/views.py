from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notification_redirect(request, notification_id):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user,
    )

    if not notification.is_read:

        notification.is_read = True
        notification.save(update_fields=["is_read"])

    return redirect(notification.url)


@login_required
def notification_list(request):

    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("classroom")
        .order_by("-created_at")
    )

    return render(
        request,
        "notifications/notification_list.html",
        {
            "notifications": notifications,
        },
    )