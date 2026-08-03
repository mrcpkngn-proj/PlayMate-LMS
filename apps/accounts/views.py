from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from .forms import RegisterForm

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