import random
import json

from decimal import Decimal

from datetime import timedelta

from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.utils import timezone
from django.urls import reverse


from .models import Answer, Attempt, Quiz, Choice, Question
from .forms import QuizForm
from .question_banks import get_question_bank

from apps.classroom.models import ClassroomMember, Classroom, Classwork
from apps.classroom.forms import ClassworkForm


def user_can_access_quiz(user, quiz):
    classroom = quiz.classwork.classroom

    if user == classroom.teacher:
        return True

    return ClassroomMember.objects.filter(
        classroom=classroom,
        student=user,
    ).exists()


@login_required
def prepare_quiz_attempt(request, quiz_id):

    mark_expired_attempts()

    quiz = get_object_or_404(Quiz, id=quiz_id)

    if not user_can_access_quiz(request.user, quiz):
        raise HttpResponseForbidden(
            "You don't have access to this quiz."
        )

    is_teacher = (
        request.user == quiz.classwork.classroom.teacher
    )

    completed_attempts = Attempt.objects.filter(
        quiz=quiz,
        student=request.user,
        is_completed=True,
    ).count()

    ongoing_attempt = Attempt.objects.filter(
        quiz=quiz,
        student=request.user,
        is_completed=False,
    ).last()

    if ongoing_attempt and ongoing_attempt.is_active():
        attempt = ongoing_attempt

    else:

        if not is_teacher and completed_attempts >= quiz.max_attempts:
            return {
                "no_attempts": True,
                "quiz": quiz,
                "attempts_used": completed_attempts,
            }

        attempt = Attempt.objects.create(
            quiz=quiz,
            student=request.user,
            score=0,
        )

    all_questions = list(
        quiz.questions.prefetch_related("choices")
    )

    if not attempt.question_order:

        questions = all_questions[:]

        if quiz.shuffle_questions:
            random.shuffle(questions)

        attempt.question_order = [q.id for q in questions]
        attempt.save()

    question_map = {
        q.id: q
        for q in all_questions
    }

    questions = [
        question_map[qid]
        for qid in attempt.question_order
        if qid in question_map
    ]

    choice_order = attempt.choice_order or {}
    changed = False

    for question in questions:

        choices = list(question.choices.all())
        key = str(question.id)

        if key not in choice_order:

            if quiz.shuffle_choices:
                random.shuffle(choices)

            choice_order[key] = [
                c.id
                for c in choices
            ]

            changed = True

        choice_map = {
            c.id: c
            for c in choices
        }

        question.shuffled_choices = [
            choice_map[cid]
            for cid in choice_order[key]
            if cid in choice_map
        ]

    if changed:
        attempt.choice_order = choice_order
        attempt.save()

    return {
        "no_attempts": False,
        "quiz": quiz,
        "attempt": attempt,
        "questions": questions,
        "completed_attempts": completed_attempts,
    }


@login_required
def quiz_list(request):

    quizzes = (
        Quiz.objects
        .select_related("classwork")
    )

    return render(
        request,
        "quiz/quiz_list.html",
        {
            "quizzes": quizzes,
        },
    )

@login_required
def quiz_create(request, classroom_id):
    classroom = get_object_or_404(
        Classroom,
        pk=classroom_id,
        teacher=request.user,
    )

    suggestions = []
    if request.method == "POST":
        topics = request.POST.get("topics")
        if topics:
            suggestions = suggest_questions(topics)
    if request.method == "POST":
        quiz_form = QuizForm(request.POST)
        classwork_form = ClassworkForm(request.POST)
        if quiz_form.is_valid() and classwork_form.is_valid():
            question_texts = request.POST.getlist("question_text[]")
            question_points = request.POST.getlist("question_points[]")
            question_types = request.POST.getlist("question_type[]")
            question_durations = request.POST.getlist("question_duration[]")

            with transaction.atomic():
                quiz = quiz_form.save(commit=False)

                classwork = classwork_form.save(commit=False)
                classwork.classroom = classroom
                classwork.work_type = "quiz"
                classwork.created_by = request.user
                classwork.save()

                quiz.classwork = classwork
                quiz.save()


                for index, question_text in enumerate(question_texts):
                    if not question_text.strip():
                        continue

                    raw_duration = question_durations[index] or "30"
                    duration_seconds = int(raw_duration)

                    question = Question.objects.create(
                        quiz=quiz,
                        text=question_text,
                        points=question_points[index] or 1,
                        answer_type=question_types[index] or "single",
                        duration=duration_seconds,
                    )

                    choice_texts = request.POST.getlist(f"choice_text_{index}[]")
                    correct_choice_indices = request.POST.getlist(f"correct_choice_{index}")

                    for choice_index, choice_text in enumerate(choice_texts):
                        if not choice_text.strip():
                            continue

                        Choice.objects.create(
                            question=question,
                            text=choice_text,
                            is_correct=str(choice_index) in correct_choice_indices,
                        )

            return redirect("classroom:classroom_classwork", pk=classroom.id,)
    else:
        quiz_form = QuizForm()
        classwork_form = ClassworkForm()

    return render(request, "quiz/quiz_full_form.html", {
        "quiz_form": quiz_form,
        "quiz_data": [],
        "suggestions": suggestions,
        "classwork_form": classwork_form,
        "classroom": classroom,
    })



@login_required
def quiz_update(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related("classwork", "classwork__classroom"),
        id=quiz_id,
        classwork__created_by=request.user,
    )

    if quiz.classwork.classroom.teacher != request.user:
        return redirect("classroom:classroom_list")
    
    quiz_data = [
        {
            "id": question.id,
            "text": question.text,
            "points": question.points,
            "answer_type": question.answer_type,
            "choices": [
                {"id": choice.id, "text": choice.text, "is_correct": choice.is_correct}
                for choice in question.choices.all()
            ],
        }
        for question in quiz.questions.prefetch_related("choices")
    ]

    if request.method == "POST":
        quiz_form = QuizForm(request.POST, instance=quiz)
        classwork_form = ClassworkForm(request.POST, instance=quiz.classwork)

        if quiz_form.is_valid() and classwork_form.is_valid():
            question_ids = request.POST.getlist("question_id[]")
            question_texts = request.POST.getlist("question_text[]")
            question_points = request.POST.getlist("question_points[]")
            question_types = request.POST.getlist("question_type[]")
            question_durations = request.POST.getlist("question_duration[]")
            with transaction.atomic():
                updated_quiz = quiz_form.save(commit=False)

                updated_classwork = classwork_form.save(commit=False)
                updated_classwork.save()

                updated_quiz.save()

                if updated_quiz.classwork.classroom.teacher != request.user:
                    return redirect("classroom:classroom_list")

                kept_question_ids = []

                for index, question_text in enumerate(question_texts):
                    if not question_text.strip():
                        continue

                    question_id = question_ids[index]
                    raw_duration = question_durations[index] or "30"
                    duration_seconds = int(raw_duration)

                    if question_id:
                        question = get_object_or_404(Question, id=question_id, quiz=quiz)
                        question.text = question_text
                        question.points = question_points[index] or 1
                        question.answer_type = question_types[index] or "single"
                        question.duration = duration_seconds
                        question.save()
                    else:
                        question = Question.objects.create(
                            quiz=quiz,
                            text=question_text,
                            points=question_points[index] or 1,
                            answer_type=question_types[index] or "single",
                            duration=duration_seconds,
                        )

                    kept_question_ids.append(question.id)

                    choice_ids = request.POST.getlist(f"choice_id_{index}[]")
                    choice_texts = request.POST.getlist(f"choice_text_{index}[]")
                    correct_choice_indices = request.POST.getlist(f"correct_choice_{index}")

                    kept_choice_ids = []
                    for choice_index, choice_text in enumerate(choice_texts):
                        if not choice_text.strip():
                            continue

                        choice_id = choice_ids[choice_index]
                        if choice_id:
                            choice = get_object_or_404(Choice, id=choice_id, question=question)
                            choice.text = choice_text
                            choice.is_correct = str(choice_index) in correct_choice_indices
                            choice.save()
                        else:
                            choice = Choice.objects.create(
                                question=question,
                                text=choice_text,
                                is_correct=str(choice_index) in correct_choice_indices,
                            )
                        kept_choice_ids.append(choice.id)

                    # delete choices not kept
                    question.choices.exclude(id__in=kept_choice_ids).delete()

                # delete questions not kept
                quiz.questions.exclude(id__in=kept_question_ids).delete()

            return redirect("classroom:classroom_classwork", pk=quiz.classwork.classroom.id,)
    else:
        quiz_form = QuizForm(instance=quiz)
        classwork_form = ClassworkForm(instance=quiz.classwork)


    return render(request, "quiz/quiz_full_form.html", {
        "quiz_form": quiz_form,
        "quiz": quiz,
        "quiz_data": quiz_data,
        "classwork_form": classwork_form,
        "classroom": quiz.classwork.classroom,
    })



@login_required
def quiz_delete(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related("classwork", "classwork__classroom"),
        id=quiz_id,
        classwork__created_by=request.user,
    )

    if quiz.classwork.classroom.teacher != request.user:
        return redirect("classroom:classroom_list")

    if request.method == "POST":
        classroom_id = quiz.classwork.classroom.id
        quiz.classwork.delete()
        return redirect("classroom:classroom_classwork", pk=classroom_id,)

    return render(request, "quiz/quiz_confirm_delete.html", {
        "quiz": quiz,
    })


@login_required
def take_quiz(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
    )

    if not user_can_access_quiz(request.user, quiz):
        raise HttpResponseForbidden(
            "You don't have access to this quiz."
        )
    
    if quiz.display_mode == "single_page":
        return take_quiz_full(request, quiz_id)

    data = prepare_quiz_attempt(request, quiz_id)

    if data["no_attempts"]:
        return render(
            request,
            "quiz/no_attempts.html",
            {
                "quiz": data["quiz"],
                "attempts_used": data["attempts_used"],
                "max_attempts": data["quiz"].max_attempts,
            },
        )
    
    attempt = data["attempt"]

    return redirect(
        "quiz:take_question",
        quiz_id=quiz_id,
        question_index=attempt.current_question,
    )

@login_required
def take_question(request, quiz_id, question_index):

    data = prepare_quiz_attempt(request, quiz_id)

    if not user_can_access_quiz(
        request.user,
        data["quiz"],
    ):
        raise HttpResponseForbidden(
            "You don't have access to this quiz."
        )

    if data["no_attempts"]:
        return render(
            request,
            "quiz/no_attempts.html",
            {
                "quiz": data["quiz"],
                "attempts_used": data["attempts_used"],
                "max_attempts": data["quiz"].max_attempts,
            }
        )

    quiz = data["quiz"]
    attempt = data["attempt"]
    questions = data["questions"]

    if question_index >= len(questions):
        return redirect(
            "quiz:quiz_result",
            attempt_id=attempt.id,
        )

    question = questions[question_index]

    choices = question.shuffled_choices

    answered_count = (
        attempt.answers.values("question_id")
        .distinct()
        .count()
    )

    total_questions = len(questions)

    progress = int(
        (answered_count / total_questions) * 100
    )

    correct_count = question.choices.filter(
        is_correct=True
    ).count()

    question_key = (
        f"attempt_{attempt.id}_question_{question.id}_start"
    )

    if question_key not in request.session:
        request.session[question_key] = (
            timezone.now().isoformat()
        )

    question_started_at = parse_datetime(
        request.session[question_key]
    )

    selected_choices = list(
        attempt.answers.filter(
            question=question
        ).values_list(
            "selected_choice_id",
            flat=True
        )
    )

    print(question.answer_type)
    print(correct_count)

    return render(
        request,
        "quiz/take_question.html",
        {
            "quiz": quiz,
            "attempt": attempt,
            "question": question,
            "choices": choices,
            "question_index": question_index,
            "total_questions": total_questions,
            "progress": progress,
            "correct_count": correct_count,
            "quiz_started_at": attempt.started_at,
            "quiz_duration": quiz.duration,
            "question_started_at": question_started_at,
            "question_duration": question.duration,
            "attempts_left": quiz.max_attempts - data["completed_attempts"],
            "selected_choices": selected_choices,
        },
    )

@login_required
def take_quiz_full(request, quiz_id):

    data = prepare_quiz_attempt(request, quiz_id)

    if not user_can_access_quiz(
        request.user,
        data["quiz"],
    ):
        raise HttpResponseForbidden(
            "You don't have access to this quiz."
        )
    if data["no_attempts"]:
        return render(
            request,
            "quiz/no_attempts.html",
            {
                "quiz": data["quiz"],
                "attempts_used": data["attempts_used"],
                "max_attempts": data["quiz"].max_attempts,
            }
        )

    questions = data["questions"]

    for question in questions:
        question.correct_count = question.choices.filter(
            is_correct=True
        ).count()

    attempt = data["attempt"]

    answered_count = attempt.answers.values(
        "question_id"
    ).distinct().count()

    progress = int(
        (answered_count / len(questions)) * 100
    )

    return render(
        request,
        "quiz/take_quiz.html",
        {
            "quiz": data["quiz"],
            "attempt": attempt,
            "questions": questions,
            "progress": progress,
            "quiz_started_at": attempt.started_at,
            "quiz_duration": data["quiz"].duration,
        },
    )


def mark_expired_attempts():
    now = timezone.now()
    for attempt in Attempt.objects.filter(is_completed=False):
        end_time = attempt.started_at + timedelta(minutes=attempt.quiz.duration)
        if now >= end_time:
            attempt.is_completed = True
            attempt.submitted_at = end_time
            attempt.save()


def calculate_multiple_choice_score(
    question,
    selected_choices,
):
    correct_choices = set(
        question.choices.filter(
            is_correct=True
        ).values_list(
            "id",
            flat=True,
        )
    )

    selected_ids = set(
        selected_choices.values_list(
            "id",
            flat=True,
        )
    )

    correct_selected = len(
        selected_ids & correct_choices
    )

    if not correct_choices:
        return Decimal("0")

    fraction = (
        Decimal(correct_selected)
        / Decimal(len(correct_choices))
    )

    return fraction * Decimal(question.points)

def score_question(attempt, question, selected_choices):

    earned_points = Decimal("0")

    if question.answer_type == "single":

        selected_choice = selected_choices.first()

        correct = (
            selected_choice is not None
            and selected_choice.is_correct
        )

        Answer.objects.create(
            attempt=attempt,
            question=question,
            selected_choice=selected_choice,
            is_correct=correct,
        )

        if correct:
            earned_points = Decimal(question.points)

    else:

        earned_points = calculate_multiple_choice_score(
            question,
            selected_choices,
        )

        for choice in selected_choices:

            Answer.objects.create(
                attempt=attempt,
                question=question,
                selected_choice=choice,
                is_correct=choice.is_correct,
            )

    return earned_points


@login_required
def submit_question(request, attempt_id, question_id, question_index):
    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
        student=request.user,
        is_completed=False,
    )

    if not user_can_access_quiz(
        request.user,
        attempt.quiz,
    ):
        raise HttpResponseForbidden(
            "You don't have access to this quiz."
        )

    question = get_object_or_404(
        Question,
        id=question_id,
        quiz=attempt.quiz,
    )

    # Prevent duplicate submissions if user refreshes
    if attempt.answers.filter(question=question).exists():
        return redirect(
            "quiz:take_quiz",
            quiz_id=attempt.quiz.id,
        )

    choice_ids = request.POST.getlist("choice")
    print("choice_ids:", choice_ids)

    selected_choices = question.choices.filter(
        id__in=choice_ids
    )

    if question.answer_type == "multiple":

        max_allowed = question.choices.filter(
            is_correct=True
        ).count()

        if selected_choices.count() > max_allowed:

            return redirect(
                "quiz:take_question",
                quiz_id=attempt.quiz.id,
                question_index=question_index,
            )

    earned_points = score_question(
        attempt,
        question,
        selected_choices,
    )

    attempt.score += earned_points

    # Store selections in session (used by results page)
    selected_by_question = request.session.get(
        "selected_by_question",
        {}
    )

    selected_by_question[str(question.id)] = list(
        selected_choices.values_list(
            "id",
            flat=True,
        )
    )

    request.session["selected_by_question"] = selected_by_question

    partial_scores = request.session.get(
        "partial_scores",
        {}
    )

    partial_scores[str(question.id)] = round(
        float(earned_points),
        2,
    )

    request.session["partial_scores"] = partial_scores

    # Advance progress
    next_index = question_index + 1
    total_questions = len(attempt.question_order)

    attempt.current_question = next_index

    if next_index >= total_questions:
        attempt.current_question = total_questions
        attempt.is_completed = True
        attempt.submitted_at = timezone.now()

    attempt.save()

    if attempt.is_completed:
        return redirect(
            "quiz:quiz_result",
            attempt_id=attempt.id,
        )

    return redirect(
        "quiz:take_quiz",
        quiz_id=attempt.quiz.id,
    )

@login_required
def submit_full_quiz(request, attempt_id):

    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
        student=request.user,
        is_completed=False,
    )

    if not user_can_access_quiz(
        request.user,
        attempt.quiz,
    ):
        raise HttpResponseForbidden(
            "You don't have access to this quiz."
        )

    questions = attempt.quiz.questions.prefetch_related("choices")

    total_score = Decimal("0")

    for question in questions:

        choice_ids = request.POST.getlist(
            f"question_{question.id}"
        )

        selected_choices = question.choices.filter(
            id__in=choice_ids
        )

        if question.answer_type == "multiple":

            max_allowed = question.choices.filter(
                is_correct=True
            ).count()

            if selected_choices.count() > max_allowed:

                return HttpResponseForbidden(
                    "Too many answers were selected."
                )

        earned_points = score_question(
            attempt,
            question,
            selected_choices,
        )

        total_score += earned_points

    attempt.score = total_score
    attempt.is_completed = True
    attempt.submitted_at = timezone.now()
    attempt.save()

    return redirect(
        "quiz:quiz_result",
        attempt_id=attempt.id,
    )

@login_required
def quiz_result(request, attempt_id):

    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
    )

    quiz = attempt.quiz
    classroom = quiz.classwork.classroom

    if (
        request.user != attempt.student
        and request.user != classroom.teacher
    ):
        raise HttpResponseForbidden(
            "You don't have permission to view this quiz result."
        )
    
    answers = attempt.answers.select_related("question", "selected_choice")
    questions = attempt.quiz.questions.prefetch_related("choices")

    # Track selected choices per question
    selected_by_question = {}
    for ans in answers:
        selected_by_question.setdefault(ans.question.id, []).append(ans.selected_choice_id)

    # Track per-question scores
    partial_scores = {}
    for question in attempt.quiz.questions.prefetch_related("choices"):
        selected_ids = set(selected_by_question.get(question.id, []))
        correct_ids = set(question.choices.filter(is_correct=True).values_list("id", flat=True))

        if question.answer_type == "single":

            if (
                len(selected_ids) == 1
                and next(iter(selected_ids)) in correct_ids
            ):
                earned = Decimal(question.points)
            else:
                earned = Decimal("0")

        else:
            earned = calculate_multiple_choice_score(
                question,
                question.choices.filter(id__in=selected_ids),
            )

        partial_scores[question.id] = round(
            float(earned),
            2,
        )

    total_points = sum(q.points for q in attempt.quiz.questions.all())

        # 🔒 Count attempts
    completed_attempts = Attempt.objects.filter(
        quiz=attempt.quiz,
        student=attempt.student,
        is_completed=True
    ).count()

    attempts_left = max(
        0,
        attempt.quiz.max_attempts - completed_attempts
    )

    is_owner = request.user == attempt.student

    is_teacher_attempt = (
        request.user == classroom.teacher
        and attempt.student == classroom.teacher
    )

    is_teacher_view = (
        request.user == classroom.teacher
        and attempt.student != classroom.teacher
    )

    if is_owner:
        return_url = reverse(
            "classroom:classroom_classwork",
            args=[attempt.quiz.classwork.classroom.id],
        )
    else:
        return_url = reverse(
            "classroom:student_quiz_attempts",
            args=[
                attempt.quiz.classwork.classroom.id,
                attempt.student.id,
                attempt.quiz.id,
            ],
        )

    return render(request, "quiz/quiz_result.html", {
        "attempt": attempt,
        "answers": answers,
        "selected_by_question": selected_by_question,
        "partial_scores": partial_scores,
        "total_points": total_points,
        "attempts_left": attempts_left,
        "questions": questions,
        "max_attempts": attempt.quiz.max_attempts,
        "is_owner": is_owner,
        "is_teacher_attempt": is_teacher_attempt,
        "is_teacher_view": is_teacher_view,
        "return_url": return_url,
    })


def suggest_questions(topics: str):
    suggestions = []
    for topic in topics.split(","):
        topic = topic.strip().lower()
        suggestions.extend(get_question_bank(topic))
    return suggestions


@login_required
def suggest_questions_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        topics = data.get("topics", "")
        suggestions = suggest_questions(topics)
        return JsonResponse({"suggestions": suggestions})
    return JsonResponse({"suggestions": []})

