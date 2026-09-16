from apps.quiz.models import Quiz, Attempt
from apps.assignment.models import Assignment, Submission

from apps.alec.analytics import (
    generate_student_report,
    generate_teacher_report,
)
from apps.alec import analytics
from apps.alec import rules

from .personality import AlecPersonality
from .memory import AlecMemory

from django.urls import reverse
from django.utils import timezone
from .alec_context import AlecContext



class SidebarBuilder:

    """
    Builds everything that appears in the ALEC sidebar.

    This class DOES NOT perform AI reasoning.
    It only gathers information and formats it for the UI.

    Student
        ↓
    Analytics
        ↓
    Rules
        ↓
    Personality
        ↓
    Sidebar Context
    """

    # =====================================================
    # PUBLIC ENTRY
    # =====================================================
    def __init__(self):
        self.context = AlecContext()

    def build(self, user, classroom, request=None):

        if classroom.teacher == user:
            sidebar = self.build_teacher_sidebar(
                user,
                classroom,
            )
        else:
            sidebar = self.build_student_sidebar(
                user,
                classroom,
            )

        if request:

            page_context = self.context.detect(
                request
            )

            contextual = self.context.build_message(
                user,
                page_context,
                sidebar,
            )

            sidebar["alec_context"] = page_context
            sidebar["alec_contextual"] = contextual

        return sidebar

    # =====================================================
    # STUDENT SIDEBAR
    # =====================================================

    def build_student_sidebar(self, student, classroom):

        personality = AlecPersonality()

        task_data = self.build_task_list(
            student,
            classroom,
        )

        task_list = task_data["tasks"]

        total_task_count = len(task_list)

        pending_task_count = task_data["pending_task_count"]

        visible_tasks = task_list[:10]

        report = generate_student_report(
            student,
            classroom,
            task_list,
            pending_task_count,
        )

        memory = AlecMemory().build(
            student,
            classroom,
            report,
            task_list,
        )

        memory_message = personality.memory_message(
            memory
        )

        event_message = personality.event_message(
            memory
        )

        mood_icon, mood_name = personality.mood(report["level"])

        return {
            # -----------------------------------------
            # Core A.L.E.C.
            # -----------------------------------------
            "alec_mode": "student",
            "alec_classroom": classroom,

            # -----------------------------------------
            # Personality
            # -----------------------------------------
            "greeting": personality.greeting(
                student.username,
                memory,
            ),
            "mission": personality.mission(
                memory
            ),
            "status_message": personality.status(
                classroom,
                memory,
            ),
            "memory_message": memory_message,
            "event_message": event_message,
            "mood_icon": mood_icon,
            "mood_name": mood_name,

            # -----------------------------------------
            # Performance
            # -----------------------------------------
            "performance": report["performance"],
            "level": report["level"],
            "risk": report["risk"],

            # -----------------------------------------
            # Progress
            # -----------------------------------------
            "progress": report["progress"],
            "summary": report["summary"],

            # -----------------------------------------
            # Learning
            # -----------------------------------------
            "learning": report["learning"],
            "study_tips": report["study_tips"],
            "analysis": report["analysis"],
            "insights": report["insights"],

            # -----------------------------------------
            # Tasks
            # -----------------------------------------
            "visible_tasks": visible_tasks,
            "task_list": task_list,
            "pending_task_count": pending_task_count,
            "total_task_count": total_task_count,
            "priority": memory["priority"],
            "overdue": memory["overdue"],
            "today": memory["today"],
            "upcoming": memory["upcoming"],

            # -----------------------------------------
            # A.L.E.C. interpretation
            # -----------------------------------------
            "strongest_area": memory["strongest_area"],
            "weakest_area": memory["weakest_area"],

            # -----------------------------------------
            # A.L.E.C. memory
            # -----------------------------------------
            "changes": memory["changes"],
            "previous_snapshot": memory["previous_snapshot"],
            "recent_events": memory["recent_events"],
        }

    # =====================================================
    # TEACHER SIDEBAR
    # =====================================================

    def build_teacher_sidebar(self, teacher, classroom):

        personality = AlecPersonality()

        # -------------------------------------------------
        # Basic classroom information
        # -------------------------------------------------

        student_count = classroom.members.count()

        assignment_count = Assignment.objects.filter(
            classwork__classroom=classroom,
        ).count()

        quiz_count = Quiz.objects.filter(
            classwork__classroom=classroom,
        ).count()

        # -------------------------------------------------
        # A.L.E.C. teacher report
        # -------------------------------------------------

        report = generate_teacher_report(
            classroom
        )

        performance = report["performance"]

        # -------------------------------------------------
        # Latest submission
        # -------------------------------------------------

        latest_submission = Submission.objects.filter(
            assignment__classwork__classroom=classroom,
        ).order_by(
            "-submitted_at"
        ).first()

        # -------------------------------------------------
        # Teacher status message
        # -------------------------------------------------

        overall = performance["classroom_average"]

        if report["high_risk_students"]:

            status_message = (
                f"{len(report['high_risk_students'])} "
                "student(s) require immediate attention."
            )

        elif report["medium_risk_students"]:

            status_message = (
                f"{len(report['medium_risk_students'])} "
                "student(s) may need additional monitoring."
            )

        elif report["pending_grading_count"]:

            status_message = (
                f"{report['pending_grading_count']} "
                "submission(s) are waiting to be graded."
            )

        elif overall >= 90:

            status_message = (
                "Classroom performance is excellent."
            )

        elif overall >= 75:

            status_message = (
                "Classroom performance is stable."
            )

        else:

            status_message = (
                "Classroom performance needs attention."
            )

        # -------------------------------------------------
        # Teacher sidebar context
        # -------------------------------------------------

        return {

            # ---------------------------------------------
            # Core A.L.E.C.
            # ---------------------------------------------

            "alec_mode": "teacher",

            "alec_classroom": classroom,

            # ---------------------------------------------
            # Classroom
            # ---------------------------------------------

            "student_count": student_count,

            "assignment_count": assignment_count,

            "quiz_count": quiz_count,

            # ---------------------------------------------
            # Teacher personality
            # ---------------------------------------------

            "greeting": personality.greeting(
                teacher.username
            ),

            "mission": (
                "Monitor classroom progress "
                "and guide student learning."
            ),

            "status_message": status_message,

            "mood_icon": "🧠",

            "mood_name": "Instructor",

            # ---------------------------------------------
            # Classroom performance
            # ---------------------------------------------

            "performance": performance,

            "classroom_average": performance[
                "classroom_average"
            ],

            "quiz_average": performance[
                "quiz_average"
            ],

            "assignment_average": performance[
                "assignment_average"
            ],

            # ---------------------------------------------
            # Students
            # ---------------------------------------------

            "students": report["students"],

            "priority_students": report[
                "priority_students"
            ],

            "high_risk_students": report[
                "high_risk_students"
            ],

            "medium_risk_students": report[
                "medium_risk_students"
            ],

            "excellent_students": report[
                "excellent_students"
            ],

            # ---------------------------------------------
            # Grading
            # ---------------------------------------------

            "pending_grading": report[
                "pending_grading"
            ],

            "pending_grading_count": report[
                "pending_grading_count"
            ],

            # ---------------------------------------------
            # Activity
            # ---------------------------------------------

            "recent_activity": report[
                "recent_activity"
            ],

            "latest_submission": latest_submission,

            # ---------------------------------------------
            # A.L.E.C. recommendations
            # ---------------------------------------------

            "recommendations": report[
                "recommendations"
            ],

            # ---------------------------------------------
            # Teacher sidebar compatibility
            # ---------------------------------------------

            "analysis": [],

            "study_tips": [],

            "task_list": [],

            "summary": (
                "Teacher classroom analytics are active."
            ),

            "learning": [],

            "insights": report[
                "recommendations"
            ],
        }

    # =====================================================
    # TASK BUILDER
    # =====================================================

    def build_task_list(self, student, classroom):

        today = timezone.now()

        submitted_ids = Submission.objects.filter(
            student=student,
            assignment__classwork__classroom=classroom,
        ).values_list(
            "assignment_id",
            flat=True,
        )

        task_list = []
        pending_task_count = 0

        # ---------------- Assignments ---------------- #

        for assignment in Assignment.objects.filter(
            classwork__classroom=classroom
        ).select_related("classwork"):

            submitted = assignment.id in submitted_ids
            due = assignment.classwork.due_date

            if submitted:

                task_list.append({
                    "type": "assignment",
                    "title": assignment.classwork.title,
                    "url": reverse(
                        "assignment:assignment_detail",
                        args=[assignment.id],
                    ),
                    "status": "submitted",
                    "due": due,
                    "label": "Completed",
                })

                continue

            pending_task_count += 1
            status = "upcoming"
            label = "No Due Date"

            if due:

                if due < today:

                    status = "overdue"
                    label = "Overdue"

                elif due.date() == today.date():

                    status = "today"
                    label = "Due Today"

                else:

                    status = "upcoming"

                    days = (
                        due.date()
                        - today.date()
                    ).days

                    label = (
                        f"In {days} day"
                        if days == 1
                        else f"In {days} days"
                    )

            task_list.append({
                "type": "assignment",
                "title": assignment.classwork.title,
                "url": reverse(
                    "assignment:assignment_detail",
                    args=[assignment.id],
                ),
                "status": status,
                "due": due,
                "label": label,
            })

        # ---------------- Quizzes ---------------- #

        for quiz in Quiz.objects.filter(
            classwork__classroom=classroom
        ).select_related("classwork"):

            completed = Attempt.objects.filter(
                quiz=quiz,
                student=student,
                is_completed=True,
            ).exists()

            due = quiz.classwork.due_date

            if completed:

                task_list.append({
                    "type": "quiz",
                    "title": quiz.classwork.title,
                    "url": reverse(
                        "quiz:quiz_detail",
                        args=[quiz.id],
                    ),
                    "status": "submitted",
                    "due": due,
                    "label": "Completed",
                })

                continue

            pending_task_count += 1
            status = "upcoming"
            label = "No Due Date"

            if due:

                if due < today:
                    status = "overdue"
                    label = "Overdue"

                elif due.date() == today.date():
                    status = "today"
                    label = "Due Today"

                else:
                    status = "upcoming"
                    days = (
                        due.date()
                        - today.date()
                    ).days

                    label = (
                        f"In {days} day"
                        if days == 1
                        else f"In {days} days"
                    )

            task_list.append({
                "type": "quiz",
                "title": quiz.classwork.title,
                "url": reverse(
                    "quiz:quiz_detail",
                    args=[quiz.id],
                ),

                "status": status,
                "due": due,
                "label": label,

            })

        priority = {
            "overdue": 0,
            "today": 1,
            "upcoming": 2,
            "submitted": 3,
        }

        task_list.sort(
            key=lambda task: (
                priority[task["status"]],
                task["due"]
                or timezone.datetime.max.replace(
                    tzinfo=timezone.get_current_timezone()
                ),
            )
        )

        return {
            "tasks": task_list,
            "pending_task_count": pending_task_count,
            "total_task_count": len(task_list),
        }