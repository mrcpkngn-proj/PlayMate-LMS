from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from .forms import RegisterForm, ProfileForm, SettingsForm
from django.contrib.auth.decorators import login_required
from .models import UserSettings


def login_view(request):
    # If already logged in, go straight to quiz dashboard
    if request.user.is_authenticated:
        return redirect("classroom:classroom_list")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("classroom:classroom_list")

    return render(request, "accounts/login.html", {"form": form})

def register_view(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            return redirect("classroom:classroom_list")

    else:

        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@login_required
def profile_view(request):

    return render(
        request,
        "accounts/profile.html",
    )


@login_required
def edit_profile(request):

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            instance=request.user,
        )

        if form.is_valid():

            form.save()

            return redirect("accounts:profile")

    else:

        form = ProfileForm(
            instance=request.user,
        )

    return render(
        request,
        "accounts/edit_profile.html",
        {
            "form": form,
        },
    )


@login_required
def settings_view(request):

    settings, created = UserSettings.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        form = SettingsForm(
            request.POST,
            instance=settings,
        )

        if form.is_valid():

            form.save()

            return redirect("accounts:settings")

    else:

        form = SettingsForm(
            instance=settings,
        )

    return render(
        request,
        "accounts/settings.html",
        {
            "form": form,
        },
    )


def password_recovery(request):
    return render(
        request,
        "accounts/password_recovery.html"
    )


def about_view(request):
    return render(
        request,
        "accounts/about.html",
    )