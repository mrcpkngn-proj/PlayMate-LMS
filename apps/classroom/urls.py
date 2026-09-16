from django.urls import path
from . import views

app_name = "classroom"

urlpatterns = [
    path("", views.classroom_list, name="classroom_list"),
    path("create/", views.create_classroom, name="create_classroom",),
    path("join/",views.join_classroom, name="join_classroom"),

    # For Student Members
    path("<int:pk>/leave/", views.leave_classroom, name="leave_classroom"),

    # For Teacher Members
    path("<int:pk>/edit/", views.edit_classroom, name="edit_classroom"),
    path("<int:pk>/delete/", views.delete_classroom, name="delete_classroom"),
    path("classroom/<int:pk>/remove/<int:user_id>/", views.remove_student, name="remove_student"),
    path("<int:pk>/announcement/<int:post_id>/edit/", views.edit_announcement, name="edit_announcement"),
    path("<int:pk>/announcement/<int:post_id>/delete/", views.delete_announcement, name="delete_announcement"),    

    #Classroom Tabs
    path( "<int:pk>/dashboard/", views.classroom_dashboard, name="classroom_dashboard"),
    path("<int:pk>/student-dashboard/", views.student_dashboard, name="student_dashboard"),
    path("<int:pk>/stream/", views.classroom_stream, name="classroom_stream"),
    path("<int:pk>/classwork/", views.classroom_classwork, name="classroom_classwork"),
    path("<int:pk>/people/", views.classroom_people, name="classroom_people"),
    path("<int:classroom_id>/grades/", views.classroom_grades, name="classroom_grades"),
    path("<int:classroom_id>/analytics/", views.classroom_analytics, name="classroom_analytics"),

    path("<int:pk>/grades/<int:student_id>/", views.student_grades, name="student_grades"),
    path("<int:pk>/grades/<int:student_id>/quiz/<int:quiz_id>/", views.student_quiz_attempts, name="student_quiz_attempts"),


]