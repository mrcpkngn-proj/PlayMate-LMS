from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [

    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("about/", views.about_view, name="about"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("settings/", views.settings_view, name="settings"),
    path("password-recovery/", views.password_recovery, name="password_recovery"),
    path("password/change/", auth_views.PasswordChangeView.as_view(template_name="accounts/password_change.html", success_url=reverse_lazy("accounts:password_change_done")),name="password_change"),
    path("password/change/done/", auth_views.PasswordChangeDoneView.as_view(template_name="accounts/password_change_done.html"), name="password_change_done",),
]