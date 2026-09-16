from apps.classroom.models import Classroom, ClassroomMember
from apps.assignment.models import Assignment
from apps.quiz.models import Quiz, Attempt

from .services import AlecService


def alec_sidebar(request):

    if not request.user.is_authenticated:
        return {}

    match = request.resolver_match

    if not match:
        return {}

    classroom = None

    # =========================================================
    # DETERMINE PAGE CONTEXT
    # =========================================================

    url_name = match.url_name or ""

    PAGE_CONTEXTS = {

        # -----------------------------------------------------
        # Classroom tabs
        # -----------------------------------------------------

        "classroom_dashboard":
            "classroom_dashboard",

        "classroom_stream":
            "classroom_stream",

        "classroom_classwork":
            "classroom_classwork",

        "classroom_people":
            "classroom_people",

        "classroom_grades":
            "classroom_grades",

        "classroom_analytics":
            "classroom_analytics",

        # -----------------------------------------------------
        # Student classroom pages
        # -----------------------------------------------------

        "student_dashboard":
            "student_dashboard",

        "student_grades":
            "student_grades",

        "student_quiz_attempts":
            "student_quiz_attempts",

        # -----------------------------------------------------
        # Other pages
        # -----------------------------------------------------

        "assignment_detail":
            "assignment",

        "quiz_detail":
            "quiz",

        "take_quiz":
            "quiz",

        "quiz_attempt":
            "attempt",
    }

    page_context = PAGE_CONTEXTS.get(
        url_name,
        "other",
    )

    # =========================================================
    # FIND CLASSROOM
    # =========================================================

    classroom_id = (
        match.kwargs.get("pk")
        or match.kwargs.get("classroom_id")
    )

    # ---------------------------------------------------------
    # Classroom URLs
    # ---------------------------------------------------------

    if classroom_id:

        try:

            classroom = Classroom.objects.get(
                pk=classroom_id
            )

        except Classroom.DoesNotExist:

            return {}

    # ---------------------------------------------------------
    # Assignment URLs
    # ---------------------------------------------------------

    elif "assignment_id" in match.kwargs:

        try:

            assignment = Assignment.objects.select_related(
                "classwork__classroom"
            ).get(
                pk=match.kwargs["assignment_id"]
            )

            classroom = assignment.classwork.classroom

            page_context = "assignment"

        except Assignment.DoesNotExist:

            return {}

    # ---------------------------------------------------------
    # Quiz URLs
    # ---------------------------------------------------------

    elif "quiz_id" in match.kwargs:

        try:

            quiz = Quiz.objects.select_related(
                "classwork__classroom"
            ).get(
                pk=match.kwargs["quiz_id"]
            )

            classroom = quiz.classwork.classroom

            page_context = "quiz"

        except Quiz.DoesNotExist:

            return {}

    # ---------------------------------------------------------
    # Attempt URLs
    # ---------------------------------------------------------

    elif "attempt_id" in match.kwargs:

        try:

            attempt = Attempt.objects.select_related(
                "quiz__classwork__classroom"
            ).get(
                pk=match.kwargs["attempt_id"]
            )

            classroom = attempt.quiz.classwork.classroom

            page_context = "attempt"

        except Attempt.DoesNotExist:

            return {}

    # =========================================================
    # VERIFY CLASSROOM MEMBERSHIP
    # =========================================================

    if classroom:

        if classroom.teacher == request.user:

            is_teacher = True

        elif ClassroomMember.objects.filter(
            classroom=classroom,
            student=request.user,
        ).exists():

            is_teacher = False

        else:

            return {}

    else:

        is_teacher = False

    # =========================================================
    # BASE CONTEXT
    # =========================================================

    context = {
        "page_context": page_context,
        "is_teacher": is_teacher,
        "alec_classroom": classroom,
    }

    # =========================================================
    # DETERMINE WHETHER A.L.E.C. ANALYTICS ARE NEEDED
    # =========================================================

    ANALYTICS_CONTEXTS = {

        # Teacher
        "classroom_dashboard",

        # Student
        "student_dashboard",

        # Classwork may use lightweight task information.
        # Remove this if your classwork page does not need it.
        "classroom_classwork",

        "classroom_analytics",
        "classroom_grades",
        "classroom_stream",
    }

    # =========================================================
    # BUILD A.L.E.C. SIDEBAR ONLY WHEN REQUIRED
    # =========================================================

    if classroom and page_context in ANALYTICS_CONTEXTS:

        alec = AlecService()

        alec_context = alec.get_sidebar_context(
            request.user,
            classroom,
            request=request,
        )

        context.update(alec_context)

    # =========================================================
    # RETURN CONTEXT
    # =========================================================

    return context