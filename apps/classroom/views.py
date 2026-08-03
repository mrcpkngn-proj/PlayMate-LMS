from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import AnnouncementForm, ClassroomForm
from .models import Classroom, ClassroomMember, Classwork, StreamPost
from django.http import Http404
from django.db.models import Avg
from apps.quiz.models import Attempt, Quiz
from apps.assignment.models import Assignment, Submission


def get_classroom_context(pk, user):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
    )

    is_teacher = classroom.teacher == user

    is_member = classroom.members.filter(
        student=user
    ).exists()

    if not is_teacher and not is_member:
        raise Http404("Classroom not found.")

    return {
        "classroom": classroom,
    }


@login_required
def classroom_list(request):
    owned = Classroom.objects.filter(teacher=request.user)
    joined = Classroom.objects.filter(members__student=request.user)

    classrooms = (owned | joined).distinct()

    return render(
        request,
        "classroom/classroom_list.html",
        {
            "classrooms": classrooms,
        },
    )

@login_required
def create_classroom(request):

    if request.method == "POST":

        form = ClassroomForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            classroom = form.save(commit=False)
            classroom.teacher = request.user
            classroom.save()

            messages.success(
                request,
                "Classroom created successfully!"
            )

            return redirect(
                "classroom:classroom_stream",
                pk=classroom.pk
            )

    else:

        form = ClassroomForm()

    return render(request, "classroom/create_classroom.html",{"form": form})


@login_required
def join_classroom(request):

    if request.method == "POST":

        code = request.POST.get("class_code", "").strip().upper()

        if not code:
            messages.error(request, "Please enter a classroom code.")
            return redirect("classroom:join_classroom")

        classroom = Classroom.objects.filter(
            class_code=code,
            is_active=True,
        ).first()

        if classroom is None:
            messages.error(request, "Invalid classroom join code.")
            return redirect("classroom:join_classroom")

        if classroom.teacher == request.user:
            messages.info(request, "You are the teacher of this classroom.")
            return redirect(
                "classroom:classroom_stream",
                pk=classroom.pk,
            )

        member, created = ClassroomMember.objects.get_or_create(
            classroom=classroom,
            student=request.user,
        )

        if created:
            messages.success(request, "Successfully joined classroom.")
        else:
            messages.info(request, "You are already a member of this classroom.")

        return redirect(
            "classroom:classroom_stream",
            pk=classroom.pk,
        )

    return render(
        request,
        "classroom/join_classroom.html",
    )


@login_required
def classroom_stream(request, pk):

    context = get_classroom_context(pk, request.user)

    classroom = context["classroom"]

    if request.method == "POST":
        if request.user == classroom.teacher:

            form = AnnouncementForm(request.POST)

            if form.is_valid():
                announcement = form.save(commit=False)
                announcement.classroom = classroom
                announcement.author = request.user
                announcement.post_type = "announcement"
                announcement.save()

                return redirect(
                    "classroom:classroom_stream",
                    pk=pk,
                )

    else:

        form = AnnouncementForm()

    context["announcement_form"] = form

    context["stream_posts"] = (
        classroom
        .stream_posts
        .select_related(
            "author",
            "assignment__classwork",
            "quiz__classwork",
        )
    )

    return render(
        request,
        "classroom/classroom_stream.html",
        context,
    )


@login_required
def classroom_people(request, pk):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
    )

    teacher = classroom.teacher

    students = (
        classroom.members
        .select_related("student")
        .order_by("student__username")
    )

    context = {
        "classroom": classroom,
        "teacher": teacher,
        "students": students,
    }

    return render(
        request,
        "classroom/classroom_people.html",
        context,
    )


@login_required
def classroom_grades(request, classroom_id):

    classroom = get_object_or_404(
        Classroom,
        id=classroom_id,
        teacher=request.user,
    )

    students = ClassroomMember.objects.select_related(
        "student"
    ).filter(
        classroom=classroom,
    )

    grade_rows = []

    for member in students:

        student = member.student

        # -------------------------
        # QUIZZES
        # -------------------------

        quiz_attempts = (
            Attempt.objects.filter(
                student=student,
                quiz__classwork__classroom=classroom,
                is_completed=True,
            )
            .select_related("quiz")
            .prefetch_related("quiz__questions")
        )

        quiz_earned = 0
        quiz_possible = 0

        for attempt in quiz_attempts:

            quiz_earned += float(attempt.score)

            quiz_possible += sum(
                question.points
                for question in attempt.quiz.questions.all()
            )

        if quiz_possible:

            quiz_average = (
                quiz_earned / quiz_possible
            ) * 100

        else:

            quiz_average = None

        # -------------------------
        # ASSIGNMENTS
        # -------------------------

        submissions = Submission.objects.filter(
            student=student,
            assignment__classwork__classroom=classroom,
            grade__isnull=False,
        ).select_related(
            "assignment"
        )

        assignment_earned = 0
        assignment_possible = 0

        for submission in submissions:

            assignment_earned += float(submission.grade)

            assignment_possible += (
                submission.assignment.points
            )

        if assignment_possible:

            assignment_average = (
                assignment_earned /
                assignment_possible
            ) * 100

        else:

            assignment_average = None

        # -------------------------
        # OVERALL
        # -------------------------

        values = [
            x for x in [
                quiz_average,
                assignment_average,
            ]
            if x is not None
        ]

        overall = (
            sum(values) / len(values)
            if values
            else None
        )

        grade_rows.append({
            "student": student,
            "quiz_average": quiz_average,
            "assignment_average": assignment_average,
            "overall": overall,
        })

    return render(
        request,
        "classroom/classroom_grades.html",
        {
            "classroom": classroom,
            "grade_rows": grade_rows,
        },
    )


@login_required
def leave_classroom(request, pk):

    classroom = get_object_or_404(Classroom, pk=pk)

    ClassroomMember.objects.filter(
        classroom=classroom,
        student=request.user,
    ).delete()

    messages.success(
        request,
        "You left the classroom."
    )

    return redirect(
        "classroom:classroom_list"
    )


@login_required
def edit_classroom(request, pk):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
        teacher=request.user,
    )

    if request.method == "POST":

        form = ClassroomForm(
            request.POST,
            request.FILES,
            instance=classroom,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Classroom updated successfully.",
            )

            return redirect(
                "classroom:classroom_stream",
                pk=classroom.pk,
            )

    else:

        form = ClassroomForm(instance=classroom)

    return render(
        request,
        "classroom/edit_classroom.html",
        {
            "form": form,
            "classroom": classroom,
        },
    )


@login_required
def delete_classroom(request, pk):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
        teacher=request.user,
    )

    if request.method == "POST":

        classroom.delete()

        messages.success(
            request,
            "Classroom deleted successfully.",
        )

        return redirect(
            "classroom:classroom_list",
        )

    return render(
        request,
        "classroom/delete_classroom.html",
        {
            "classroom": classroom,
        },
    )


@login_required
def remove_student(request, pk, user_id):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
        teacher=request.user,
    )

    ClassroomMember.objects.filter(
        classroom=classroom,
        student_id=user_id,
    ).delete()

    messages.success(
        request,
        "Student removed."
    )

    return redirect(
        "classroom:classroom_people",
        pk=pk,
    )


@login_required
def classroom_classwork(request, pk):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
    )

    classworks = (
        Classwork.objects
        .filter(classroom=classroom)
        .select_related("created_by")
        .prefetch_related(
            "quiz",
            "assignment",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "classroom/classroom_classwork.html",
        {
            "classroom": classroom,
            "classworks": classworks,

        },
    )


@login_required
def student_grades(request, pk, student_id):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
        teacher=request.user,
    )

    User = get_user_model()

    student = get_object_or_404(
        User,
        id=student_id,
    )

    quizzes = Quiz.objects.filter(
        classwork__classroom=classroom
    ).prefetch_related("questions")

    quiz_rows = []

    for quiz in quizzes:

        attempts = Attempt.objects.filter(
            quiz=quiz,
            student=student,
            is_completed=True,
        ).order_by("submitted_at")

        if not attempts.exists():
            continue

        total_points = sum(
            question.points
            for question in quiz.questions.all()
        )

        percentages = []

        highest_percentage = 0

        for attempt in attempts:

            percentage = (
                float(attempt.score) /
                total_points * 100
                if total_points
                else 0
            )

            percentages.append(percentage)

            highest_percentage = max(
                highest_percentage,
                percentage,
            )

        quiz_rows.append({

            "quiz": quiz,

            "highest_percentage": highest_percentage,

            "attempt_count": attempts.count(),

        })

    submissions = (
        Submission.objects.filter(
            student=student,
            assignment__classwork__classroom=classroom,
        )
        .select_related(
            "assignment",
            "assignment__classwork",
        )
    )

    return render(
        request,
        "classroom/student_grades.html",
        {
            "classroom": classroom,
            "student": student,
            "quiz_rows": quiz_rows,
            "submissions": submissions,
        },
    )


@login_required
def student_quiz_attempts(request, pk, student_id, quiz_id):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
        teacher=request.user,
    )

    User = get_user_model()
    
    student = get_object_or_404(
        User,
        id=student_id,
    )

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        classwork__classroom=classroom,
    )

    attempts = (
        Attempt.objects.filter(
            student=student,
            quiz=quiz,
            is_completed=True,
        )
        .order_by("submitted_at")
    )

    total_points = sum(
        question.points
        for question in quiz.questions.all()
    )

    attempt_rows = []

    for attempt in attempts:

        percentage = (
            float(attempt.score) /
            total_points * 100
            if total_points
            else 0
        )

        attempt_rows.append({
            "attempt": attempt,
            "percentage": percentage,
        })

    return render(
        request,
        "classroom/student_quiz_attempts.html",
        {
            "classroom": classroom,
            "student": student,
            "quiz": quiz,
            "attempt_rows": attempt_rows,
            "total_points": total_points,
        },
    )


@login_required
def classroom_dashboard(request, pk):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
    )

    is_teacher = classroom.teacher == request.user

    is_member = classroom.members.filter(
        student=request.user
    ).exists()

    if not is_teacher and not is_member:
        raise Http404("Classroom not found.")

    
    if is_teacher:
        students = ClassroomMember.objects.filter(
            classroom=classroom
        )
        quizzes = Quiz.objects.filter(
            classwork__classroom=classroom
        )

        quiz_averages = []

        for quiz in quizzes:

            attempts = Attempt.objects.filter(
                quiz=quiz,
                is_completed=True,
            )

            total_points = sum(
                question.points
                for question in quiz.questions.all()
            )

            if attempts.exists() and total_points:

                average_score = attempts.aggregate(
                    avg=Avg("score")
                )["avg"]

                average_percentage = (
                    float(average_score)
                    / total_points
                ) * 100

            else:

                average_percentage = 0

            quiz_averages.append({

                "quiz": quiz,

                "average": average_percentage,

                "attempts": attempts.count(),

            })

        assignments = Assignment.objects.filter(
            classwork__classroom=classroom
        )

        attempts = Attempt.objects.filter(
            quiz__classwork__classroom=classroom,
            is_completed=True,
        )

        submissions = Submission.objects.filter(
            assignment__classwork__classroom=classroom,
        )

        total_students = students.count()

        total_quizzes = quizzes.count()

        total_assignments = assignments.count()

        total_submissions = submissions.count()

        expected_submissions = (
            total_students * total_assignments
        )

        if expected_submissions:

            submission_rate = (
                total_submissions /
                expected_submissions
            ) * 100

        else:

            submission_rate = 0

        students_needing_attention = []

        for member in students:

            student = member.student

            attempts = Attempt.objects.filter(
                student=student,
                quiz__classwork__classroom=classroom,
                is_completed=True,
            )

            percentages = []

            for attempt in attempts:

                total_points = sum(
                    q.points
                    for q in attempt.quiz.questions.all()
                )

                if total_points:
                    percentages.append(
                        float(attempt.score) /
                        total_points * 100
                    )

            average = (
                sum(percentages) / len(percentages)
                if percentages else 0
            )

            missing_assignments = Assignment.objects.filter(
                classwork__classroom=classroom
            ).exclude(
                submissions__student=student
            ).count()

            if average < 75 or missing_assignments > 0:

                students_needing_attention.append({

                    "student": student,

                    "average": average,

                    "missing": missing_assignments,

                })

            recent_submissions = (
                Submission.objects.filter(
                    assignment__classwork__classroom=classroom,
                )
                .select_related(
                    "student",
                    "assignment__classwork",
                )
                .order_by("-submitted_at")[:5]
            )

            recent_attempts = (
                Attempt.objects.filter(
                    quiz__classwork__classroom=classroom,
                    is_completed=True,
                )
                .select_related(
                    "student",
                    "quiz__classwork",
                )
                .order_by("-submitted_at")[:5]
            )

            recent_posts = (
                StreamPost.objects.filter(
                    classroom=classroom,
                )
                .select_related("author")
                .order_by("-created_at")[:5]
            )

    else:

        quizzes = Quiz.objects.filter(
            classwork__classroom=classroom
        )

        assignments = Assignment.objects.filter(
            classwork__classroom=classroom
        )

        attempts = Attempt.objects.filter(
            student=request.user,
            quiz__classwork__classroom=classroom,
            is_completed=True,
        ).select_related(
            "quiz",
            "quiz__classwork",
        )

        submissions = Submission.objects.filter(
            student=request.user,
            assignment__classwork__classroom=classroom,
        ).select_related(
            "assignment",
            "assignment__classwork",
        )

        submitted_ids = submissions.values_list(
            "assignment_id",
            flat=True,
        )

        pending_assignments = assignments.exclude(
            id__in=submitted_ids,
        )

        percentages = []

        for attempt in attempts:

            total_points = sum(
                q.points
                for q in attempt.quiz.questions.all()
            )

            if total_points:

                percentages.append(
                    float(attempt.score)
                    / total_points
                    * 100
                )

        quiz_average = (
            sum(percentages)
            / len(percentages)
            if percentages
            else 0
        )

        latest_announcement = (
            StreamPost.objects.filter(
                classroom=classroom,
                post_type="announcement",
            )
            .select_related("author")
            .order_by("-created_at")
            .first()
        )

        context = {
            "classroom": classroom,
            "is_teacher": False,
            "quiz_average": quiz_average,
            "completed_quizzes": attempts.count(),
            "completed_assignments": submissions.count(),
            "pending_assignments": pending_assignments,
            "latest_announcement": latest_announcement,
            "recent_submissions": recent_submissions,
            "recent_attempts": recent_attempts,
            "recent_posts": recent_posts,
        }

        return render(
            request,
            "classroom/classroom_dashboard.html",
            context,
        )

    context = {
        "classroom": classroom,
        "is_teacher": True,
        "total_students": total_students,
        "total_quizzes": total_quizzes,
        "total_assignments": total_assignments,
        "submission_rate": submission_rate,
        "quiz_averages": quiz_averages,
        "students_needing_attention": students_needing_attention,
    }

    return render(
        request,
        "classroom/classroom_dashboard.html",
        context,
    )


@login_required
def edit_announcement(request, pk, post_id):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
        teacher=request.user,
    )

    announcement = get_object_or_404(
        StreamPost,
        id=post_id,
        classroom=classroom,
        post_type="announcement",
    )

    if request.method == "POST":

        form = AnnouncementForm(
            request.POST,
            instance=announcement,
        )

        if form.is_valid():

            form.save()

            return redirect(
                "classroom:classroom_stream",
                pk=pk,
            )

    else:

        form = AnnouncementForm(
            instance=announcement,
        )

    return render(
        request,
        "classroom/edit_announcement.html",
        {
            "classroom": classroom,
            "form": form,
        },
    )


@login_required
def delete_announcement(request, pk, post_id):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
        teacher=request.user,
    )

    announcement = get_object_or_404(
        StreamPost,
        id=post_id,
        classroom=classroom,
        post_type="announcement",
    )

    if request.method == "POST":

        announcement.delete()

        return redirect(
            "classroom:classroom_stream",
            pk=pk,
        )

    return render(
        request,
        "classroom/delete_announcement.html",
        {
            "classroom": classroom,
            "announcement": announcement,
        },
    )

#helper function to calculate teacher analytics
def teacher_analytics(request, classroom):

    quizzes = Quiz.objects.filter(
        classwork__classroom=classroom
    )

    assignments = Assignment.objects.filter(
        classwork__classroom=classroom
    )

    students = ClassroomMember.objects.filter(
        classroom=classroom
    )

    quiz_rows = []

    for quiz in quizzes:

        attempts = Attempt.objects.filter(
            quiz=quiz,
            is_completed=True,
        )

        total_points = sum(
            q.points
            for q in quiz.questions.all()
        )

        if attempts.exists() and total_points:

            average = (
                attempts.aggregate(
                    avg=Avg("score")
                )["avg"]
                / total_points
            ) * 100

        else:

            average = 0

        quiz_rows.append({

            "quiz": quiz,

            "average": average,

            "attempts": attempts.count(),

        })

    context = {

        "classroom": classroom,

        "is_teacher": True,

        "student_count": students.count(),

        "assignment_count": assignments.count(),

        "quiz_rows": quiz_rows,

    }

    return render(

        request,

        "classroom/classroom_analytics.html",

        context,

    )

#helper function to calculate student analytics
def student_analytics(request, classroom):

    attempts = Attempt.objects.filter(
        student=request.user,
        quiz__classwork__classroom=classroom,
        is_completed=True,
    ).select_related(
        "quiz",
        "quiz__classwork",
    )

    percentages = []

    for attempt in attempts:

        total = sum(
            q.points
            for q in attempt.quiz.questions.all()
        )

        if total:

            percentages.append({

                "quiz": attempt.quiz,

                "percentage": (
                    float(attempt.score)
                    / total
                ) * 100,

            })

    context = {

        "classroom": classroom,

        "is_teacher": False,

        "percentages": percentages,

    }

    return render(

        request,

        "classroom/classroom_analytics.html",

        context,

    )

@login_required
def classroom_analytics(request, pk):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
    )

    is_teacher = classroom.teacher == request.user

    is_member = classroom.members.filter(
        student=request.user
    ).exists()

    if not is_teacher and not is_member:
        raise Http404()

    if is_teacher:

        return teacher_analytics(
            request,
            classroom,
        )

    return student_analytics(
        request,
        classroom,
    )


@login_required
def student_dashboard(request, pk):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
    )

    if not ClassroomMember.objects.filter(
        classroom=classroom,
        student=request.user,
    ).exists():
        raise Http404()

    attempts = (
        Attempt.objects.filter(
            student=request.user,
            quiz__classwork__classroom=classroom,
            is_completed=True,
        )
        .select_related(
            "quiz",
            "quiz__classwork",
        )
        .order_by("-submitted_at")
    )

    percentages = []

    for attempt in attempts:

        total_points = sum(
            q.points
            for q in attempt.quiz.questions.all()
        )

        if total_points:
            percentages.append(
                float(attempt.score) /
                total_points * 100
            )

    quiz_average = (
        sum(percentages) / len(percentages)
        if percentages else 0
    )

    completed_quizzes = attempts.count()

    completed_assignments = Submission.objects.filter(
        student=request.user,
        assignment__classwork__classroom=classroom,
    ).count()

    pending_assignments = Assignment.objects.filter(
        classwork__classroom=classroom,
    ).exclude(
        submissions__student=request.user,
    ).select_related(
        "classwork",
    )

    latest_announcement = (
        StreamPost.objects.filter(
            classroom=classroom,
            post_type="announcement",
        )
        .select_related("author")
        .order_by("-created_at")
        .first()
    )

    recent_attempt_rows = []

    for attempt in attempts[:5]:

        total_points = sum(
            q.points
            for q in attempt.quiz.questions.all()
        )

        percentage = (
            float(attempt.score) / total_points * 100
            if total_points else 0
        )

        recent_attempt_rows.append({
            "attempt": attempt,
            "percentage": percentage,
        })

    return render(
        request,
        "classroom/student_dashboard.html",
        {
            "classroom": classroom,
            "quiz_average": quiz_average,
            "completed_quizzes": completed_quizzes,
            "completed_assignments": completed_assignments,
            "pending_assignments": pending_assignments,
            "recent_attempt_rows": recent_attempt_rows,
            "latest_announcement": latest_announcement,
        },
    )