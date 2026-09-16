from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import AnnouncementForm, ClassroomForm
from .models import Classroom, ClassroomMember, Classwork, StreamPost
from django.http import Http404
from apps.quiz.models import Attempt, Quiz
from apps.assignment.models import Assignment, Submission
from django.utils import timezone
from django.urls import reverse
from itertools import chain
from apps.alec.services import AlecService
from apps.notifications.utils import create_notification
from apps.alec.memory import AlecMemory

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
                members = ClassroomMember.objects.filter(
                    classroom=classroom
                ).select_related("student")

                for member in members:

                    create_notification(

                        recipient=member.student,

                        classroom=classroom,

                        title=f"📢 {classroom.name}",

                        message=announcement.message[:50] + (
                            "..." if len(announcement.message) > 50 else ""
                        ),

                        url=reverse(
                            "classroom:classroom_stream",
                            args=[classroom.id],
                        ),

                    )

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

    AlecMemory().record_event(

        student=request.user,

        classroom=classroom,

        event_type="classroom_revisited",

        title=classroom.name,

        description="Student opened the classroom.",)


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

    assignments = Assignment.objects.filter(
        classwork__classroom=classroom
    ).select_related("classwork")

    quizzes = Quiz.objects.filter(
        classwork__classroom=classroom
    ).prefetch_related("questions")

    grade_rows = []

    for member in students:

        quiz_percentages = []

        for quiz in quizzes:

            attempts = Attempt.objects.filter(
                student=member.student,
                quiz=quiz,
                is_completed=True,
            )

            if not attempts.exists():
                continue

            total_points = sum(
                q.points
                for q in quiz.questions.all()
            )

            if total_points == 0:
                continue

            best_attempt = max(
                attempts,
                key=lambda a: float(a.score)
            )

            percentage = (
                float(best_attempt.score)
                / total_points
            ) * 100

            quiz_percentages.append(percentage)

        quiz_average = (
            sum(quiz_percentages) / len(quiz_percentages)
            if quiz_percentages
            else None
        )

        # -------------------------
        # ASSIGNMENTS
        # -------------------------

        earned = 0
        possible = 0

        pending = 0
        missing = 0

        now = timezone.now()

        for assignment in assignments:

            submission = Submission.objects.filter(
                assignment=assignment,
                student=member.student,
            ).first()

            if submission:

                if submission.grade is not None:

                    earned += float(submission.grade)
                    possible += assignment.points

                else:
                    pending += 1

            else:

                if assignment.classwork.due_date:

                    if assignment.classwork.due_date < now:
                        missing += 1
                    else:
                        pending += 1
                else:
                    pending += 1

        assignment_average = (
            earned / possible * 100
            if possible
            else None
        )

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
            "student": member.student,
            "quiz_average": quiz_average,
            "assignment_average": assignment_average,
            "pending": pending,
            "missing": missing,
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

    is_teacher = (
        request.user == classroom.teacher
    )

    classworks = (
        Classwork.objects
        .filter(classroom=classroom)
        .select_related("created_by")
        .prefetch_related(
            "quiz__questions",
            "assignment",
        )
        .order_by("-created_at")
    )

    if not is_teacher:

        # -----------------------------------------
        # Load ALL quiz attempts for this student
        # -----------------------------------------

        attempts = (
            Attempt.objects
            .filter(
                student=request.user,
                is_completed=True,
                quiz__classwork__classroom=classroom,
            )
            .select_related("quiz")
        )

        attempts_by_quiz = {}

        for attempt in attempts:

            attempts_by_quiz.setdefault(
                attempt.quiz_id,
                []
            ).append(attempt)

        # -----------------------------------------
        # Load ALL assignment submissions once
        # -----------------------------------------

        submissions = (
            Submission.objects
            .filter(
                student=request.user,
                assignment__classwork__classroom=classroom,
            )
            .select_related("assignment")
        )

        submissions_by_assignment = {

            submission.assignment_id: submission

            for submission in submissions

        }

        # -----------------------------------------
        # Attach data to each classwork
        # -----------------------------------------

        for classwork in classworks:

            # ==========================
            # QUIZZES
            # ==========================

            if (
                classwork.work_type == "quiz"
                and hasattr(classwork, "quiz")
            ):

                quiz = classwork.quiz

                quiz_attempts = attempts_by_quiz.get(
                    quiz.id,
                    [],
                )

                classwork.best_score = None
                classwork.total_points = 0
                classwork.best_percentage = None

                if quiz_attempts:

                    best_attempt = max(
                        quiz_attempts,
                        key=lambda a: float(a.score),
                    )

                    total_points = sum(
                        question.points
                        for question in quiz.questions.all()
                    )

                    classwork.best_score = best_attempt.score
                    classwork.total_points = total_points

                    if total_points:

                        classwork.best_percentage = (
                            float(best_attempt.score)
                            / total_points
                        ) * 100

            # ==========================
            # ASSIGNMENTS
            # ==========================

            elif (
                classwork.work_type == "assignment"
                and hasattr(classwork, "assignment")
            ):

                assignment = classwork.assignment

                submission = submissions_by_assignment.get(
                    assignment.id
                )

                classwork.submission = submission
                classwork.assignment_status = None

                if submission:

                    if submission.grade is not None:

                        classwork.assignment_status = "graded"

                    else:

                        classwork.assignment_status = "submitted"

                else:

                    if (
                        classwork.due_date
                        and classwork.due_date < timezone.now()
                    ):

                        classwork.assignment_status = "missing"

                    else:

                        classwork.assignment_status = "not_submitted"

    return render(
        request,
        "classroom/classroom_classwork.html",
        {
            "classroom": classroom,
            "classworks": classworks,
            "is_teacher": is_teacher,
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
        students = ClassroomMember.objects.filter(classroom=classroom)

        quizzes = Quiz.objects.filter(
            classwork__classroom=classroom
        )

        assignments = Assignment.objects.filter(
            classwork__classroom=classroom
        )

        recent_submissions = (
            Submission.objects
            .filter(
                assignment__classwork__classroom=classroom
            )
            .select_related(
                "student",
                "assignment__classwork",
            )
        )

        recent_attempts = (
            Attempt.objects
            .filter(
                quiz__classwork__classroom=classroom,
                is_completed=True,
            )
            .select_related(
                "student",
                "quiz__classwork",
            )
        )

        recent_posts = (
            StreamPost.objects
            .filter(
                classroom=classroom
            )
            .select_related(
                "author",
            )
        )

        activity_feed = []

        for submission in recent_submissions:

            activity_feed.append({

                "icon": "📁",

                "time": submission.submitted_at,

                "user": (
                    submission.student.get_full_name()
                    or submission.student.username
                ),

                "text": (
                    f"submitted "
                    f"{submission.assignment.classwork.title}"
                ),

            })

        for attempt in recent_attempts:

            activity_feed.append({

                "icon": "📝",

                "time": attempt.submitted_at,

                "user": (
                    attempt.student.get_full_name()
                    or attempt.student.username
                ),

                "text": (
                    f"completed "
                    f"{attempt.quiz.classwork.title}"
                ),

            })

        activity_feed.sort(

            key=lambda x: x["time"],

            reverse=True,

        )

        activity_feed = activity_feed[:20]

        context = {

            "classroom": classroom,

            "is_teacher": True,

            "total_students": students.count(),

            "total_quizzes": quizzes.count(),

            "total_assignments": assignments.count(),

            "recent_submissions": recent_submissions,

            "recent_attempts": recent_attempts,

            "recent_posts": recent_posts,

            "activity_feed": activity_feed,

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


@login_required
def classroom_analytics(request, classroom_id):

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

    quizzes = (
        Quiz.objects.filter(
            classwork__classroom=classroom,
        )
        .prefetch_related("questions")
    )

    assignments = Assignment.objects.filter(
        classwork__classroom=classroom,
    )

    student_stats = []

    excellent = 0
    good = 0
    fair = 0
    attention = 0
    missing_assignments = 0

    # --------------------------------------------------
    # Build statistics for every student
    # --------------------------------------------------

    for member in students:

        student = member.student

        quiz_percentages = []

        # -----------------------------
        # Quiz averages
        # -----------------------------

        for quiz in quizzes:

            attempts = Attempt.objects.filter(
                quiz=quiz,
                student=student,
                is_completed=True,
            )

            if not attempts.exists():
                continue

            total_points = sum(
                q.points
                for q in quiz.questions.all()
            )

            if total_points == 0:
                continue

            best = max(
                attempts,
                key=lambda a: float(a.score)
            )

            quiz_percentages.append(
                float(best.score)
                / total_points
                * 100
            )

        quiz_average = (
            sum(quiz_percentages)
            / len(quiz_percentages)
            if quiz_percentages
            else 0
        )

        # -----------------------------
        # Missing assignments
        # -----------------------------

        assignment_percentages = []

        missing = 0

        for assignment in assignments:

            submission = Submission.objects.filter(
                assignment=assignment,
                student=student,
            ).first()

            if submission:

                if (
                    submission.grade is not None
                    and assignment.points > 0
                ):

                    percentage = (
                        float(submission.grade)
                        / assignment.points
                    ) * 100

                    assignment_percentages.append(
                        percentage
                    )

            else:

                if (
                    assignment.classwork.due_date
                    and assignment.classwork.due_date < timezone.now()
                ):

                    missing += 1

        assignment_average = (

            sum(assignment_percentages)

            / len(assignment_percentages)

            if assignment_percentages

            else 0

        )

        averages = []

        if quiz_percentages:
            averages.append(quiz_average)

        if assignment_percentages:
            averages.append(assignment_average)

        overall_student_average = (

            sum(averages)

            / len(averages)

            if averages

            else 0

        )

        missing_assignments += missing

        student_stats.append({

            "student": student,

            "quiz_average": quiz_average,

            "assignment_average": assignment_average,

            "overall_average": overall_student_average,

            "missing": missing,

        })

        # -----------------------------
        # Doughnut groups
        # -----------------------------

        if quiz_average >= 90:
            excellent += 1

        elif quiz_average >= 85:
            good += 1

        elif quiz_average >= 75:
            fair += 1

        else:
            attention += 1

    overall_average = (
        sum(
            row["overall_average"]
            for row in student_stats
        )
        / len(student_stats)
        if student_stats else 0
    )

    highest_average = max(
        (
            row["overall_average"]
            for row in student_stats
        ),
        default=0,
    )

    lowest_average = min(
        (
            row["overall_average"]
            for row in student_stats
        ),
        default=0,
    )
    student_count = students.count()
    assignment_count = assignments.count()
    quiz_count = quizzes.count()

    # --------------------------------------------------
    # Students needing attention
    # --------------------------------------------------

    attention_students = []

    for row in student_stats:

        reasons = []

        if row["quiz_average"] < 75:
            reasons.append("Low quiz average")

        if row["missing"] > 0:
            reasons.append(
                f"{row['missing']} missing assignment(s)"
            )

        if reasons:

            row["reason"] = ", ".join(reasons)

            attention_students.append(row)

    attention_students.sort(
        key=lambda x: (
            x["quiz_average"],
            -x["missing"],
        )
    )

    top_student = None

    if student_stats:

        top_student = max(
            student_stats,
            key=lambda x: x["overall_average"]
        )


    if attention_students:

        analytics_message = (
            f"{len(attention_students)} student(s) "
            f"currently require intervention."
        )

    else:

        analytics_message = (
            "No students currently require intervention."
        )
    # --------------------------------------------------
    # Quiz chart
    # --------------------------------------------------

    quiz_chart = []

    for quiz in quizzes:
        total_points = sum(
            q.points
            for q in quiz.questions.all()
        )
        if total_points == 0:
            continue
        scores = []

        for member in students:
            attempts = Attempt.objects.filter(
                quiz=quiz,
                student=member.student,
                is_completed=True,
            )

            if not attempts.exists():
                continue

            best = max(
                attempts,
                key=lambda a: float(a.score)
            )

            scores.append(
                float(best.score)
                / total_points
                * 100
            )

            completed = scores.__len__()

            completion_rate = (
                completed / students.count() * 100
                if students.count()
                else 0
            )

        quiz_chart.append({
            "title": quiz.classwork.title,
            "average": (
                sum(scores)
                / len(scores)
                if scores
                else 0
            ),
            "completion_rate": completion_rate
        })

    assignment_chart = []

    student_total = students.count()

    for assignment in assignments:

        submitted = Submission.objects.filter(
            assignment=assignment
        ).count()

        rate = (
            submitted
            / student_total
            * 100
            if student_total else 0
        )

        assignment_chart.append({

            "title": assignment.classwork.title,

            "rate": rate,

            "submitted": submitted,

            "expected": student_total,

        })

    total_attempts = Attempt.objects.filter(
        quiz__classwork__classroom=classroom,
        is_completed=True,
    ).count()

    total_submissions = Submission.objects.filter(
        assignment__classwork__classroom=classroom,
    ).count()

    average_attempts = (
        total_attempts / quizzes.count()
        if quizzes.count()
        else 0
    )

    return render(
        request,
        "classroom/classroom_analytics.html",

        {
            "classroom": classroom,
            "attention_students": attention_students,
            "missing_assignments": missing_assignments,
            "excellent": excellent,
            "good": good,
            "fair": fair,
            "attention": attention,
            "quiz_chart": quiz_chart,
            "overall_average": overall_average,
            "highest_average": highest_average,
            "lowest_average": lowest_average,

            "assignment_chart": assignment_chart,

            "total_attempts": total_attempts,
            "total_submissions": total_submissions,
            "average_attempts": average_attempts,

            "students_at_risk": len(attention_students),
            "student_count": student_count,
            "assignment_count": assignment_count,
            "quiz_count": quiz_count,

            "top_student": top_student,

            "analytics_message": analytics_message,
        },
    )


@login_required
def student_dashboard(request, pk):

    classroom = get_object_or_404(
        Classroom,
        pk=pk,
    )

    if not ClassroomMember.objects.filter(classroom=classroom, student=request.user,).exists():
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

    latest_announcement = (
        StreamPost.objects.filter(
            classroom=classroom,
            post_type="announcement",
        )
        .select_related("author")
        .order_by("-created_at")
        .first()
    )

    alec = AlecService()

    alec_context = alec.get_sidebar_context(
        request.user,
        classroom,
    )

    print("===== ALEC CONTEXT =====")
    print(alec_context)
    print("========================")

    recent_attempt_rows = []

    for attempt in attempts[:5]:

        percentage = alec.quiz_percentage(attempt)

        recent_attempt_rows.append({
            "attempt": attempt,
            "percentage": percentage,
        })

    return render(
        request,
        "classroom/student_dashboard.html",
        {
            "classroom": classroom,
            "recent_attempt_rows": recent_attempt_rows,
            "latest_announcement": latest_announcement,
            "alec": alec_context,

        },
    )