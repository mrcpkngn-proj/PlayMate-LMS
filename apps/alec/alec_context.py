from apps.classroom.models import Classroom
from apps.assignment.models import Assignment
from apps.quiz.models import Quiz, Attempt
from apps.assignment.models import Submission
from django.utils import timezone


class AlecContext:

    def detect(self, request):

        match = request.resolver_match

        if not match:
            return self.empty()

        kwargs = match.kwargs
        url_name = match.url_name or ""

        # ---------------------------------------------
        # Attempt
        # ---------------------------------------------

        if "attempt_id" in kwargs:

            try:
                attempt = (
                    Attempt.objects
                    .select_related(
                        "quiz",
                        "quiz__classwork",
                        "quiz__classwork__classroom",
                    )
                    .get(pk=kwargs["attempt_id"])
                )

                return {
                    "page_type": "attempt",
                    "url_name": url_name,
                    "object": attempt,
                    "quiz": attempt.quiz,
                    "assignment": None,
                    "classroom": (
                        attempt.quiz.classwork.classroom
                    ),
                }

            except Attempt.DoesNotExist:
                return self.empty()

        # ---------------------------------------------
        # Quiz
        # ---------------------------------------------

        if "quiz_id" in kwargs:

            try:
                quiz = (
                    Quiz.objects
                    .select_related(
                        "classwork",
                        "classwork__classroom",
                    )
                    .get(pk=kwargs["quiz_id"])
                )

                return {
                    "page_type": "quiz",
                    "url_name": url_name,
                    "object": quiz,
                    "quiz": quiz,
                    "assignment": None,
                    "classroom": (
                        quiz.classwork.classroom
                    ),
                }

            except Quiz.DoesNotExist:
                return self.empty()

        # ---------------------------------------------
        # Assignment
        # ---------------------------------------------

        if "assignment_id" in kwargs:

            try:
                assignment = (
                    Assignment.objects
                    .select_related(
                        "classwork",
                        "classwork__classroom",
                    )
                    .get(pk=kwargs["assignment_id"])
                )

                return {
                    "page_type": "assignment",
                    "url_name": url_name,
                    "object": assignment,
                    "quiz": None,
                    "assignment": assignment,
                    "classroom": (
                        assignment.classwork.classroom
                    ),
                }

            except Assignment.DoesNotExist:
                return self.empty()

        # ---------------------------------------------
        # Classroom
        # ---------------------------------------------

        classroom_id = (
            kwargs.get("classroom_id")
            or kwargs.get("pk")
        )

        if classroom_id:

            try:
                classroom = (
                    Classroom.objects
                    .get(pk=classroom_id)
                )

                return {
                    "page_type": "classroom",
                    "url_name": url_name,
                    "object": classroom,
                    "quiz": None,
                    "assignment": None,
                    "classroom": classroom,
                }

            except Classroom.DoesNotExist:
                return self.empty()

        return self.empty()

    def empty(self):

        return {
            "page_type": "unknown",
            "url_name": "",
            "object": None,
            "quiz": None,
            "assignment": None,
            "classroom": None,
        }

    def build_message(
        self,
        user,
        context,
        sidebar,
    ):
        page_type = context["page_type"]

        if page_type == "quiz":
            return self.quiz_message(
                user,
                context,
                sidebar,
            )

        if page_type == "assignment":
            return self.assignment_message(
                user,
                context,
                sidebar,
            )

        if page_type == "attempt":
            return self.attempt_message(
                user,
                context,
                sidebar,
            )

        if page_type == "classroom":
            return self.classroom_message(
                user,
                context,
                sidebar,
            )

        return self.default_message(
            user,
            sidebar,
        )

    def quiz_message(
        self,
        user,
        context,
        sidebar,
    ):

        quiz = context["quiz"]

        if not quiz:
            return {
                "title": "Quiz",
                "message": "I'm monitoring this quiz.",
                "priority": "normal",
            }

        # Teacher
        if sidebar.get("alec_mode") == "teacher":

            return {
                "title": "Quiz Monitoring",
                "message": (
                    f"I'm monitoring student activity "
                    f"for '{quiz.classwork.title}'."
                ),
                "priority": "normal",
            }

        # Student
        attempts = Attempt.objects.filter(
            quiz=quiz,
            student=user,
            is_completed=True,
        )

        if attempts.exists():

            latest = attempts.order_by(
                "-submitted_at"
            ).first()

            return {
                "title": "Quiz Progress",
                "message": (
                    f"You've already completed "
                    f"'{quiz.classwork.title}'. "
                    f"Your latest score was "
                    f"{latest.score}."
                ),
                "priority": "normal",
            }

        return {
            "title": "Current Quiz",
            "message": (
                f"You're viewing '{quiz.classwork.title}'. "
                "Review the instructions carefully before starting."
            ),
            "priority": "normal",
        }


    def assignment_message(
        self,
        user,
        context,
        sidebar,
    ):

        assignment = context["assignment"]

        if not assignment:
            return {
                "title": "Assignment",
                "message": "I'm monitoring this assignment.",
                "priority": "normal",
            }

        if sidebar.get("alec_mode") == "teacher":

            return {
                "title": "Assignment Monitoring",
                "message": (
                    f"I'm monitoring submissions for "
                    f"'{assignment.classwork.title}'."
                ),
                "priority": "normal",
            }

        submission = (
            Submission.objects
            .filter(
                assignment=assignment,
                student=user,
            )
            .first()
        )

        if submission:

            if submission.grade is not None:

                return {
                    "title": "Assignment Result",
                    "message": (
                        f"You received a grade for "
                        f"'{assignment.classwork.title}'. "
                        "Review your feedback to improve future work."
                    ),
                    "priority": "normal",
                }

            return {
                "title": "Assignment Submitted",
                "message": (
                    f"Your submission for "
                    f"'{assignment.classwork.title}' "
                    "is waiting for grading."
                ),
                "priority": "normal",
            }

        due = assignment.classwork.due_date

        if due and due < timezone.now():

            return {
                "title": "Overdue Assignment",
                "message": (
                    f"'{assignment.classwork.title}' is overdue. "
                    "Completing it should be your priority."
                ),
                "priority": "high",
            }

        return {
            "title": "Current Assignment",
            "message": (
                f"You're working with "
                f"'{assignment.classwork.title}'. "
                "Make sure to review the instructions before submitting."
            ),
            "priority": "normal",
        }


    def attempt_message(
        self,
        user,
        context,
        sidebar,
    ):

        attempt = context["object"]

        if not attempt:
            return {
                "title": "Quiz Mode",
                "message": "Stay focused and work through each question carefully.",
                "priority": "normal",
            }

        quiz = attempt.quiz

        if sidebar.get("alec_mode") == "teacher":

            return {
                "title": "Quiz Attempt",
                "message": (
                    f"A student is working on "
                    f"'{quiz.classwork.title}'."
                ),
                "priority": "normal",
            }

        progress = sidebar.get("progress", {})
        trend = progress.get("trend")

        if trend == "improving":

            message = (
                "Your recent quiz performance is improving. "
                "Keep that momentum going."
            )

        elif trend == "declining":

            message = (
                "Your recent quiz performance has declined. "
                "Read each question carefully and avoid rushing."
            )

        else:

            message = (
                "Stay focused and work through each question carefully."
            )

        return {
            "title": "Quiz Mode",
            "message": message,
            "priority": "normal",
        }


    def classroom_message(
        self,
        user,
        context,
        sidebar,
    ):

        if sidebar.get("alec_mode") == "teacher":

            high_risk = len(
                sidebar.get(
                    "high_risk_students",
                    [],
                )
            )

            pending = sidebar.get(
                "pending_grading_count",
                0,
            )

            if high_risk:

                return {
                    "title": "Classroom Alert",
                    "message": (
                        f"{high_risk} student(s) currently "
                        "require immediate attention."
                    ),
                    "priority": "high",
                }

            if pending:

                return {
                    "title": "Grading Reminder",
                    "message": (
                        f"{pending} submission(s) "
                        "are waiting to be graded."
                    ),
                    "priority": "normal",
                }

            return {
                "title": "Classroom Status",
                "message": (
                    "Classroom performance is currently stable."
                ),
                "priority": "normal",
            }

        overdue = sidebar.get("overdue", [])

        if overdue:

            return {
                "title": "Classroom Priority",
                "message": (
                    f"You have {len(overdue)} overdue task(s). "
                    "Let's get them back on track."
                ),
                "priority": "high",
            }

        pending = sidebar.get(
            "pending_task_count",
            0,
        )

        if pending:

            return {
                "title": "Classroom Progress",
                "message": (
                    f"You have {pending} pending task(s). "
                    "Keep working through them."
                ),
                "priority": "normal",
            }

        return {
            "title": "Classroom Status",
            "message": (
                "You're currently up to date with your classroom work."
            ),
            "priority": "normal",
        }