from django.urls import path
from . import views

app_name = "assignment"

urlpatterns = [
    #Assignment CRUD
    path("classroom/<int:classroom_id>/create/", views.assignment_create, name="assignment_create"),
    path("<int:assignment_id>/edit/", views.assignment_update, name="assignment_update"),
    path("<int:assignment_id>/delete/", views.assignment_delete, name="assignment_delete"),

    path("<int:assignment_id>/", views.assignment_detail, name="assignment_detail"),
    path("attachment/<int:attachment_id>/delete/", views.attachment_delete, name="attachment_delete"),
    path("<int:assignment_id>/submissions/", views.submission_list, name="submission_list"),
    path("submission/<int:submission_id>/grade/", views.grade_submission, name="grade_submission"),

]