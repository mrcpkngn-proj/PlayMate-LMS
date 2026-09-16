from .sidebar import SidebarBuilder
from . import analytics


class AlecService:
    """
    =========================================================
    A.L.E.C.
    AI-enhanced Learning Environment Core

    Public service facade.

    Views and other Django apps should communicate with
    A.L.E.C. through this class rather than importing its
    internal modules directly.

    Internal modules:
        - analytics.py
        - sidebar.py
        - personality.py
        - rules.py
    =========================================================
    """

    def __init__(self):
        self.sidebar = SidebarBuilder()

    # =====================================================
    # SIDEBAR
    # =====================================================

    def get_sidebar_context(
        self,
        user,
        classroom,
        request=None,
    ):

        return self.sidebar.build(
            user,
            classroom,
            request=request,
        )

    # =====================================================
    # STUDENT ANALYTICS
    # =====================================================

    def calculate_student_performance(
        self,
        student,
        classroom,
    ):
        """
        Calculate quiz, assignment, and overall performance.
        """

        return analytics.calculate_student_performance(
            student,
            classroom,
        )

    def analyze_progress(
        self,
        student,
        classroom,
    ):
        """
        Analyze recent quiz performance and determine
        whether the student is improving, stable,
        declining, or new.
        """

        return analytics.analyze_progress(
            student,
            classroom,
        )

    def analyze_student(
        self,
        performance,
        task_list,
    ):
        """
        Generate analytical observations from student
        performance and classroom tasks.
        """

        return analytics.analyze_student(
            performance,
            task_list,
        )

    def get_performance_level(
        self,
        average,
    ):
        """
        Return the performance classification for an average.
        """

        return analytics.get_performance_level(
            average,
        )

    # =====================================================
    # QUIZ HELPERS
    # =====================================================

    def quiz_percentage(
        self,
        attempt,
    ):
        """
        Calculate the percentage score of a quiz attempt.
        """

        return analytics._quiz_percentage(
            attempt,
        )

    # =====================================================
    # TEACHER ANALYTICS
    # =====================================================

    def generate_teacher_report(
        self,
        classroom,
    ):
        """
        Generate the analytical report used by
        the teacher A.L.E.C. sidebar.
        """

        return analytics.generate_teacher_report(
            classroom
        )

    def get_teacher_student_status(
        self,
        classroom,
    ):
        """
        Return performance and risk information
        for every student in the classroom.
        """

        return analytics.get_teacher_student_status(
            classroom
        )

    def get_teacher_priority_students(
        self,
        classroom,
    ):
        """
        Return students ordered by attention priority.
        """

        return analytics.get_teacher_priority_students(
            classroom
        )

    def get_teacher_pending_grading(
        self,
        classroom,
    ):
        """
        Return ungraded student submissions.
        """

        return analytics.get_teacher_pending_grading(
            classroom
        )
