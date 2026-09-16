from django.db.models import Avg, Count
from . import rules
from django.utils import timezone
from apps.quiz.models import Quiz
from apps.quiz.models import Attempt
from apps.assignment.models import Submission, Assignment



def _average(values):
    """
    Safely calculate an average.

    Returns 0 when the list is empty.
    """

    return (
        sum(values) / len(values)
        if values else 0
    )

def _quiz_percentage(attempt):

    total_points = sum(

        question.points

        for question in attempt.quiz.questions.all()

    )

    if total_points == 0:

        return 0

    return (

        float(attempt.score)

        / total_points

        * 100

    )


def get_performance_level(average):
    return rules.get_performance_level(average)


def calculate_student_performance(student, classroom):

    quiz_percentages = []

    quizzes = (
        Quiz.objects.filter(
            classwork__classroom=classroom
        )
        .prefetch_related("questions")
    )

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

        best_attempt = max(
            attempts,
            key=lambda a: float(a.score)
        )

        quiz_percentages.append(_quiz_percentage(best_attempt))

    quiz_average = _average(
        quiz_percentages
    )

    assignment_percentages = []

    submissions = Submission.objects.filter(
        student=student,
        assignment__classwork__classroom=classroom,
    )

    for submission in submissions:

        if submission.grade is None:
            continue

        if submission.assignment.points == 0:
            continue

        percentage = (
            float(submission.grade)
            / submission.assignment.points
            * 100
        )

        assignment_percentages.append(percentage)

    assignment_average = _average(
        assignment_percentages
    )

    overall_average = _average([
        avg
        for avg, scores in (
            (quiz_average, quiz_percentages),
            (assignment_average, assignment_percentages),
        )
        if scores
    ])

    return {

        "quiz_average": quiz_average,

        "assignment_average": assignment_average,

        "overall_average": overall_average,

        "completed_quizzes": len(quiz_percentages),

        "graded_assignments": len(assignment_percentages),

    }


def analyze_student(performance, task_list):

    quiz_average = performance["quiz_average"]

    assignment_average = performance["assignment_average"]

    overall_average = performance["overall_average"]

    completed_quizzes = performance["completed_quizzes"]

    graded_assignments = performance["graded_assignments"]

    analysis = []

    if overall_average >= 90:
        analysis.append(
            "Excellent overall performance. Continue maintaining your current study habits."
        )

    if quiz_average >= 80 and assignment_average < 75:
        analysis.append(
            "Quiz performance is strong, but assignment grades are reducing the overall average."
        )

    if quiz_average < 75 and assignment_average >= 80:
        analysis.append(
            "Assignment submission is good, but your quiz scores are reducing the overall average."
        )

    overdue = sum(
        1
        for task in task_list
        if task["status"] == "overdue"
    )

    if overdue:
        analysis.append(
            f"You currently have {overdue} overdue task(s). Completing them should be your highest priority."
        )

    if completed_quizzes == 0:
        analysis.append(
            "No quizzes have been completed yet."
        )

    if graded_assignments == 0:
        analysis.append(
            "No graded assignments are available yet."
        )

    if not analysis:

        analysis.append(

            "Your learning progress appears stable with no major concerns."

        )

    return analysis


def analyze_progress(student, classroom):
    RECENT_ATTEMPTS = 10
    attempts = list(
        Attempt.objects.filter(
            student=student,
            quiz__classwork__classroom=classroom,
            is_completed=True,
        )
        .select_related(
            "quiz",
            "quiz__classwork",
        )
        .order_by("-submitted_at")[:RECENT_ATTEMPTS]
    )

    attempts.reverse()

    if len(attempts) < 2:

        return {

            "trend": "new",

            "message":
                "Not enough quiz history to identify a learning trend.",

            "change": 0,

        }

    midpoint = len(attempts)//2

    older = attempts[:midpoint]

    recent = attempts[midpoint:]

    old_average = _average(
        [
            _quiz_percentage(a)
            for a in older
        ]
    )

    recent_average = _average(
        [
            _quiz_percentage(a)
            for a in recent
        ]
    )

    change = recent_average - old_average

    if change >= 5:

        trend = "improving"

        message = (
            f"Your quiz performance has improved compared to your earlier attempts."
        )

    elif change <= -5:

        trend = "declining"

        message = (
            f"Your quiz performance has dropped by {abs(change):.1f}% compared to your earlier attempts."
        )

    else:

        trend = "stable"

        message = (
            "Your quiz performance has remained consistent."
        )

    return {

        "trend": trend,

        "message": message,

        "change": change,

    }

def generate_student_report(student, classroom, task_list, pending_task_count):
    """
    Build the complete analytical report for one student
    inside one classroom.
    """

    performance = calculate_student_performance(
        student,
        classroom,
    )

    progress = analyze_progress(
        student,
        classroom,
    )

    analysis = analyze_student(
        performance,
        task_list,
    )

    overdue_count = sum(
        task["status"] == "overdue"
        for task in task_list
    )

    level = rules.get_performance_level(
        performance["overall_average"]
    )

    risk = rules.get_risk_level(
        performance["overall_average"],
        overdue_count,
    )

    summary = rules.get_summary(
        level,
        progress["trend"],
    )

    learning = rules.learning_recommendations(
        performance,
        overdue_count,
    )

    pending_task_message = rules.get_pending_task_recommendation(
        pending_task_count
    )

    insights = rules.learning_insights(
        performance,
    )

    study_tips = rules.get_study_recommendations(
        performance,
        task_list,
    )

    return {
        "performance": performance,
        "progress": progress,
        "analysis": analysis,
        "study_tips": study_tips,
        "pending_task_message": pending_task_message,
        "level": level,
        "risk": risk,
        "summary": summary,
        "learning": learning,
        "insights": insights,
    }


def calculate_teacher_classroom_performance(classroom):
    """
    Calculate aggregate classroom performance.

    Returns:
        - classroom average
        - quiz average
        - assignment average
        - student count
        - students with completed work
    """

    student_reports = []

    for member in classroom.members.select_related("student"):
        student = member.student

        performance = calculate_student_performance(
            student,
            classroom,
        )

        student_reports.append({
            "student": student,
            "performance": performance,
        })

    overall_scores = [
        item["performance"]["overall_average"]
        for item in student_reports
        if (
            item["performance"]["completed_quizzes"] > 0
            or item["performance"]["graded_assignments"] > 0
        )
    ]

    quiz_scores = [
        item["performance"]["quiz_average"]
        for item in student_reports
        if item["performance"]["completed_quizzes"] > 0
    ]

    assignment_scores = [
        item["performance"]["assignment_average"]
        for item in student_reports
        if item["performance"]["graded_assignments"] > 0
    ]

    return {
        "student_count": len(student_reports),

        "classroom_average": _average(
            overall_scores
        ),

        "quiz_average": _average(
            quiz_scores
        ),

        "assignment_average": _average(
            assignment_scores
        ),

        "students_with_data": len(
            overall_scores
        ),

        "student_reports": student_reports,
    }


def get_teacher_student_status(classroom):
    """
    Classify students by performance and risk.
    """

    classroom_data = calculate_teacher_classroom_performance(
        classroom
    )

    students = []

    for item in classroom_data["student_reports"]:

        student = item["student"]
        performance = item["performance"]

        overdue_count = 0

        submissions = Submission.objects.filter(
            student=student,
            assignment__classwork__classroom=classroom,
        )

        submitted_assignment_ids = submissions.values_list(
            "assignment_id",
            flat=True,
        )

        for assignment in Assignment.objects.filter(
            classwork__classroom=classroom
        ).select_related("classwork"):

            if assignment.id in submitted_assignment_ids:
                continue

            due = assignment.classwork.due_date

            if due and due < timezone.now():
                overdue_count += 1

        risk = rules.get_risk_level(
            performance["overall_average"],
            overdue_count,
        )

        level = rules.get_performance_level(
            performance["overall_average"],
        )

        students.append({
            "student": student,
            "performance": performance,
            "risk": risk,
            "level": level,
            "overdue_count": overdue_count,
        })

    return students


def get_teacher_priority_students(classroom):
    """
    Return students who require the most attention first.
    """

    students = get_teacher_student_status(
        classroom
    )

    risk_priority = {
        "High": 0,
        "Medium": 1,
        "Low": 2,
    }

    students.sort(
        key=lambda item: (
            risk_priority[item["risk"]],
            item["performance"]["overall_average"],
            -item["overdue_count"],
        )
    )

    return students


def get_teacher_activity(classroom, limit=5):
    """
    Return recent classroom activity.
    """

    submissions = list(
        Submission.objects.filter(
            assignment__classwork__classroom=classroom,
        )
        .select_related(
            "student",
            "assignment",
            "assignment__classwork",
        )
        .order_by("-submitted_at")[:limit]
    )

    attempts = list(
        Attempt.objects.filter(
            quiz__classwork__classroom=classroom,
            is_completed=True,
        )
        .select_related(
            "student",
            "quiz",
            "quiz__classwork",
        )
        .order_by("-submitted_at")[:limit]
    )

    activity = []

    for submission in submissions:
        activity.append({
            "type": "assignment_submitted",
            "student": submission.student,
            "title": submission.assignment.classwork.title,
            "timestamp": submission.submitted_at,
            "object": submission,
        })

    for attempt in attempts:
        activity.append({
            "type": "quiz_completed",
            "student": attempt.student,
            "title": attempt.quiz.classwork.title,
            "timestamp": attempt.submitted_at,
            "object": attempt,
        })

    activity.sort(
        key=lambda item: item["timestamp"],
        reverse=True,
    )

    return activity[:limit]


def get_teacher_pending_grading(classroom):
    """
    Return assignments that have been submitted
    but have not yet been graded.
    """

    return list(
        Submission.objects.filter(
            assignment__classwork__classroom=classroom,
            grade__isnull=True,
        )
        .select_related(
            "student",
            "assignment",
            "assignment__classwork",
        )
        .order_by("submitted_at")
    )


def generate_teacher_report(classroom):
    """
    Build the complete analytical report used by
    the teacher version of A.L.E.C.
    """

    classroom_performance = (
        calculate_teacher_classroom_performance(
            classroom
        )
    )

    students = get_teacher_student_status(
        classroom
    )

    priority_students = get_teacher_priority_students(
        classroom
    )

    pending_grading = get_teacher_pending_grading(
        classroom
    )

    activity = get_teacher_activity(
        classroom
    )

    high_risk_students = [
        student
        for student in students
        if student["risk"] == "High"
    ]

    medium_risk_students = [
        student
        for student in students
        if student["risk"] == "Medium"
    ]

    excellent_students = [
        student
        for student in students
        if student["level"] == "Excellent"
    ]

    recommendations = rules.teacher_recommendations(
        {
            "overall_average":
                classroom_performance[
                    "classroom_average"
                ],

            "quiz_average":
                classroom_performance[
                    "quiz_average"
                ],

            "assignment_average":
                classroom_performance[
                    "assignment_average"
                ],
        },

        (
            "High"
            if high_risk_students
            else "Medium"
            if medium_risk_students
            else "Low"
        ),

        high_risk_count=len(
            high_risk_students
        ),

        medium_risk_count=len(
            medium_risk_students
        ),

        pending_grading_count=len(
            pending_grading
        ),
    )

    priority_students = priority_students[:5]

    return {
        "performance": classroom_performance,

        "students": students,

        "priority_students": priority_students,

        "high_risk_students": high_risk_students,

        "medium_risk_students": medium_risk_students,

        "excellent_students": excellent_students,

        "pending_grading": pending_grading,

        "pending_grading_count":
            len(pending_grading),

        "recent_activity": activity,

        "recommendations": recommendations,
    }