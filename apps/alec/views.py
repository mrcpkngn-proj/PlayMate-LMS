from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def alec_home(request):
    return render(request, "alec/home.html")