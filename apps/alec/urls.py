from django.urls import path
from . import views

app_name = "alec"

urlpatterns = [
    path("", views.alec_home, name="home"),
]