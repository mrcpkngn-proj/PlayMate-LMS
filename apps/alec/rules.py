"""
=========================================================
A.L.E.C.
AI-enhanced Learning Environment Core

Central rule engine.

This file contains ONLY business rules.
No database queries should exist here.
=========================================================
"""

# ---------------------------------------------------------
# Performance Thresholds
# ---------------------------------------------------------

EXCELLENT = 90
GOOD = 85
FAIR = 75

PASSING_GRADE = FAIR

HIGH_RISK_LIMIT = 60


# ---------------------------------------------------------
# Performance Levels
# ---------------------------------------------------------

def get_performance_level(overall_average):
    """
    Returns the student's current performance level.
    """

    if overall_average >= EXCELLENT:
        return "Excellent"

    if overall_average >= GOOD:
        return "Good"

    if overall_average >= FAIR:
        return "Fair"

    return "Needs Attention"


# ---------------------------------------------------------
# Risk Levels
# ---------------------------------------------------------

def get_risk_level(overall_average, missing_tasks):

    if overall_average < HIGH_RISK_LIMIT:
        return "High"

    if overall_average < PASSING_GRADE or missing_tasks >= 2:
        return "Medium"

    return "Low"


# ---------------------------------------------------------
# Trend Messages
# ---------------------------------------------------------

def get_trend_message(trend, change):

    if trend == "improving":
        return (
            f"Your recent quiz performance improved compared to earlier attempts."
        )

    if trend == "declining":
        return (
            f"Your recent quiz performance declined by "
            f"{abs(change):.1f}%."
        )

    return (
        "Your recent quiz performance has remained consistent."
    )


# ---------------------------------------------------------
# Stable Performance Messages
# ---------------------------------------------------------

def get_stable_message(level):

    messages = {

        "Excellent":
            "Outstanding consistency! You're maintaining excellent performance.",

        "Good":
            "Your performance has remained consistently good. Keep aiming even higher.",

        "Fair":
            "Your progress is steady. A little more practice could move you into the Good category.",

        "Needs Attention":
            "Your performance has remained below the target level. Regular review and completing missing work will help improve your results.",

    }

    return messages[level]


# ---------------------------------------------------------
# Study Recommendation
# ---------------------------------------------------------

def get_study_recommendation(overall_average):

    if overall_average >= EXCELLENT:

        return (
            "Excellent work! Continue challenging yourself with more advanced activities."
        )

    if overall_average >= FAIR:

        return (
            "Keep reviewing recent lessons to strengthen your understanding."
        )

    if overall_average >= HIGH_RISK_LIMIT:

        return (
            "Spend extra time reviewing quiz mistakes and teacher feedback."
        )

    return (
        "Focus on completing missing work and reviewing your weakest lessons first."
    )


# ---------------------------------------------------------
# Overall AI Summary
# ---------------------------------------------------------

def get_summary(level, trend):

    summaries = {

        ("Excellent", "improving"):
            "Outstanding! Your performance is excellent and continues to improve.",

        ("Excellent", "stable"):
            "Excellent performance maintained consistently.",

        ("Excellent", "declining"):
            "Your performance is still excellent, but a slight decline has been detected.",

        ("Good", "improving"):
            "Good performance with steady improvement.",

        ("Good", "stable"):
            "Good performance maintained consistently.",

        ("Good", "declining"):
            "Good performance, but your recent results have declined.",

        ("Fair", "improving"):
            "You're improving steadily. Keep practicing.",

        ("Fair", "stable"):
            "Your performance is stable but has room for improvement.",

        ("Fair", "declining"):
            "Your performance has started to decline. Consider reviewing previous lessons.",

        ("Needs Attention", "improving"):
            "You're making progress. Keep working consistently.",

        ("Needs Attention", "stable"):
            "Your performance remains below expectations.",

        ("Needs Attention", "declining"):
            "Immediate attention is recommended to improve your learning progress.",

    }

    return summaries[(level, trend)]

def learning_recommendations(performance, overdue_tasks):

    recommendations = []

    quiz = performance["quiz_average"]
    assignment = performance["assignment_average"]
    overall = performance["overall_average"]

    if overdue_tasks:
        recommendations.append(
            "Complete overdue activities before starting new lessons."
        )

    if quiz < 75:
        recommendations.append(
            "Review previous quiz topics and retry practice quizzes."
        )

    if assignment < 75:
        recommendations.append(
            "Read teacher feedback carefully before submitting future assignments."
        )

    if overall >= 90:
        recommendations.append(
            "You did an excellent job with all assigned activities. You deserve a treat!"
        )

    if not recommendations:
        recommendations.append(
            "Continue following your current study routine."
        )

    return recommendations

def teacher_recommendations(
    performance,
    risk,
    high_risk_count=0,
    medium_risk_count=0,
    pending_grading_count=0,
):
    """
    Generate classroom-level recommendations
    for the teacher version of A.L.E.C.
    """

    recommendations = []

    overall = performance["overall_average"]
    quiz = performance["quiz_average"]
    assignment = performance["assignment_average"]

    # -------------------------------------------------
    # Student risk
    # -------------------------------------------------

    if high_risk_count > 0:

        recommendations.append(
            f"{high_risk_count} student(s) are currently "
            "at high risk. Consider providing immediate "
            "individual support."
        )

    elif medium_risk_count > 0:

        recommendations.append(
            f"{medium_risk_count} student(s) may benefit "
            "from additional practice or monitoring."
        )

    # -------------------------------------------------
    # Pending grading
    # -------------------------------------------------

    if pending_grading_count > 0:

        recommendations.append(
            f"{pending_grading_count} submission(s) are "
            "waiting to be graded."
        )

    # -------------------------------------------------
    # Classroom performance
    # -------------------------------------------------

    if overall < 60:

        recommendations.append(
            "Classroom performance is below the target. "
            "Review difficult topics and consider "
            "additional learning activities."
        )

    elif overall < 75:

        recommendations.append(
            "Classroom performance has room for improvement. "
            "Consider providing additional practice activities."
        )

    elif overall >= 90:

        recommendations.append(
            "The class is performing excellently. "
            "Continue maintaining the current learning activities."
        )

    # -------------------------------------------------
    # Quiz vs assignment performance
    # -------------------------------------------------

    if quiz + 10 < assignment:

        recommendations.append(
            "Quiz performance is noticeably lower than "
            "assignment performance. Consider providing "
            "additional quiz practice."
        )

    elif assignment + 10 < quiz:

        recommendations.append(
            "Assignment performance is noticeably lower "
            "than quiz performance. Consider reviewing "
            "written activities and assignment requirements."
        )

    # -------------------------------------------------
    # Balanced performance
    # -------------------------------------------------

    if not recommendations:

        recommendations.append(
            "Classroom performance appears stable. "
            "Continue monitoring student progress."
        )

    return recommendations


def learning_insights(performance):

    insights = []

    quiz = performance["quiz_average"]
    assignment = performance["assignment_average"]
    overall = performance["overall_average"]

    insights.append(
        f"Overall classroom performance is {overall:.1f}%."
    )

    if quiz > assignment + 10:

        insights.append(
            "Quiz performance is significantly stronger than assignment performance."
        )

    elif assignment > quiz + 10:

        insights.append(
            "Assignment performance is stronger than quiz performance."
        )

    else:

        insights.append(
            "Quiz and assignment performance are balanced."
        )

    if overall >= 90:

        insights.append(
            "Current performance level exceeds classroom expectations."
        )

    elif overall >= 75:

        insights.append(
            "Current performance meets classroom expectations."
        )

    else:

        insights.append(
            "Current performance is below the expected learning outcome."
        )

    return insights


def get_study_recommendations(performance, task_list):
    quiz_average = performance["quiz_average"]

    assignment_average = performance["assignment_average"]

    overall_average = performance["overall_average"]

    study_tips = []

    overdue_tasks = [
        task for task in task_list
        if task["status"] == "overdue"
    ]

    today_tasks = [
        task for task in task_list
        if task["status"] == "today"
    ]

    upcoming_tasks = [
        task for task in task_list
        if task["status"] == "upcoming"
    ]
    if overdue_tasks:
        study_tips.append(
            f"You have {len(overdue_tasks)} overdue task(s). Complete them first."
        )

    if today_tasks:
        study_tips.append(
            f"You have {len(today_tasks)} task(s) due today."
        )

    if upcoming_tasks:
        study_tips.append(
            f"You have {len(upcoming_tasks)} upcoming task(s)."
        )

    if task_list:
        study_tips.append(
            "Complete your upcoming tasks before their due dates."
        )

    if overall_average < 75:
        study_tips.append(
            "Your overall performance is below the target. Spend time reviewing previous lessons."
        )

    elif overall_average >= 90:
        study_tips.append(
            "Excellent work! Keep maintaining your progress."
        )

    if quiz_average < 75:
        study_tips.append(
            "Quiz scores are below average right now. Review previous lessons before taking more quizzes."
        )

    if assignment_average < 75:
        study_tips.append(
            "Some assignment grades could be improved. Review teacher feedback before your next submission."
        )

    if not task_list and quiz_average > 75:

        study_tips.append(
            "Excellent work! Keep maintaining your progress."
        )
                
    if not study_tips:

        study_tips.append(
            "You're making steady progress. Stay consistent."
        )

    return study_tips


def get_pending_task_recommendation(pending_task_count):

    if pending_task_count >= 4:

        return (
            f"Urgent! You have {pending_task_count} pending tasks. "
            "Consider completing them before starting new activities."
        )

    elif pending_task_count > 0:

        return (
            f"You have {pending_task_count} pending task"
            f"{'s' if pending_task_count != 1 else ''}. "
            "Keep working through them to stay on track."
        )

    return (
        "You have no pending tasks. Great job staying up to date!"
    )