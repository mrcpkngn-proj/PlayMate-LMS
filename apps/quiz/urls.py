from django.urls import path
from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.quiz_list, name="quiz_list"),

    #Quiz CRUD
    path("classroom/<int:classroom_id>/create/", views.quiz_create, name="quiz_create"),
    path("<int:quiz_id>/edit/", views.quiz_update, name="quiz_update"),
    path("<int:quiz_id>/delete/", views.quiz_delete, name="quiz_delete"),

    path("quiz/<int:quiz_id>/", views.take_quiz, name="take_quiz"),
    path("quiz/<int:quiz_id>/detail/", views.quiz_detail, name="quiz_detail"),
    path("quiz/<int:quiz_id>/question/<int:question_index>/", views.take_question, name="take_question"),
    path("quiz/<int:attempt_id>/submit/<int:question_id>/<int:question_index>/", views.submit_question, name="submit_question"),
    path("quiz/result/<int:attempt_id>/", views.quiz_result, name="quiz_result"),
    path("attempt/<int:attempt_id>/submit/", views.submit_full_quiz, name="submit_full_quiz"),


    path("suggest_questions/", views.suggest_questions_view, name="suggest_questions_view")
]