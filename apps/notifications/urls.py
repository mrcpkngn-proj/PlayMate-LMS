from django.urls import path
from . import views


app_name = "notifications"

urlpatterns = [

    path("notification/<int:notification_id>/",
        views.notification_redirect,
        name="notification_redirect",
    ),
    path("notification/",
        views.notification_list,
        name="notification_list",
    ),

]