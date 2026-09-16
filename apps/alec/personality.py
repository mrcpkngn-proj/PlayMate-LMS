import random
from django.utils import timezone


class AlecPersonality:

    def greeting(self, username=None, memory=None):

        hour = timezone.localtime().hour

        if hour < 12:
            greeting = "Good morning"

        elif hour < 18:
            greeting = "Good afternoon"

        else:
            greeting = "Good evening"

        if memory:

            if memory["overdue"]:

                return f"{greeting}, {username}. We have unfinished work."

            if memory["progress"]["trend"] == "improving":

                return f"{greeting}, {username}. Nice improvement lately."

            if memory["performance"]["overall_average"] >= 90:

                return f"{greeting}, {username}. Outstanding work."

        return f"{greeting}, {username}."

    def mission(self, memory):

        priority = memory.get("priority")

        if not priority:
            return "No active missions."

        if isinstance(priority, list):
            return "Mission data unavailable."

        return (
            f"{priority['title']}\n"
            f"{priority['message']}"
        )

    def status(self, classroom, memory):

        return self.contextual_message(memory)

    def mood(self, level):

        moods = {

            "Excellent":
                ("😄", "Confident"),

            "Good":
                ("🙂", "Optimistic"),

            "Fair":
                ("😐", "Observing"),

            "Needs Attention":
                ("🤔", "Concerned"),
        }

        return moods[level]
    

    def contextual_message(self, memory):

        overdue = len(memory["overdue"])

        today = len(memory["today"])

        performance = memory["performance"]["overall_average"]

        trend = memory["progress"]["trend"]

        if overdue:

            return random.choice([

                f"I detected {overdue} overdue task(s).",

                "Priority override activated.",

                "Let's recover your progress."

            ])

        if today:

            return random.choice([

                f"You have {today} task(s) due today.",

                "Today's objectives are waiting.",

                "Mission control recommends finishing today's work."

            ])

        if trend == "improving":

            return random.choice([

                "I'm seeing improvement.",

                "Performance trajectory is increasing.",

                "Nice work. Keep this momentum."

            ])

        if performance >= 90:

            return random.choice([

                "Outstanding performance detected.",

                "Your learning efficiency is exceptional.",

                "You're becoming one of my top students."

            ])

        return random.choice([

            "Everything looks stable.",

            "Monitoring classroom activity.",

            "Awaiting your next objective."

        ])

    def memory_message(self, memory):

        changes = memory.get(
            "changes",
            {}
        )

        if changes.get("is_first_visit"):

            return (
                "This is my first recorded "
                "snapshot of your progress."
            )

        overall_change = changes.get(
            "overall_change",
            0,
        )

        overdue_change = changes.get(
            "overdue_change",
            0,
        )

        completed_quizzes_change = changes.get(
            "completed_quizzes_change",
            0,
        )

        graded_assignments_change = changes.get(
            "graded_assignments_change",
            0,
        )

        if overdue_change < 0:

            return (
                "Nice work. You've reduced "
                "your unfinished work."
            )

        if overall_change >= 3:

            return (
                f"Your overall performance increased "
                f"by {overall_change:.1f} percentage points."
            )

        if overall_change <= -3:

            return (
                f"I noticed your overall performance "
                f"dropped by {abs(overall_change):.1f} points."
            )

        if completed_quizzes_change > 0:

            return (
                f"You've completed "
                f"{completed_quizzes_change} "
                f"additional quiz"
                f"{'zes' if completed_quizzes_change != 1 else ''}."
            )

        if graded_assignments_change > 0:

            return (
                f"You've completed "
                f"{graded_assignments_change} "
                f"additional assignment"
                f"{'s' if graded_assignments_change != 1 else ''}."
            )

        return (
            "Your progress is stable. "
            "I'm continuing to monitor your learning."
        )

    def event_message(self, memory):

        events = memory.get(
            "recent_events",
            [],
        )

        if not events:
            return None

        event = events[0]

        # --------------------------------------------------
        # OVERALL PERFORMANCE IMPROVED
        # --------------------------------------------------

        if event.event_type == "performance_improved":

            change = (
                event.metadata.get("change", 0)
                if event.metadata
                else 0
            )

            return (
                f"Your overall performance improved "
                f"by {change:.1f} percentage points."
            )

        # --------------------------------------------------
        # OVERALL PERFORMANCE DECLINED
        # --------------------------------------------------

        if event.event_type == "performance_declined":

            change = (
                event.metadata.get("change", 0)
                if event.metadata
                else 0
            )

            return (
                f"Your overall performance decreased "
                f"by {abs(change):.1f} percentage points."
            )

        # --------------------------------------------------
        # QUIZ PERFORMANCE
        # --------------------------------------------------

        if event.event_type == "quiz_performance_changed":

            change = (
                event.metadata.get("change", 0)
                if event.metadata
                else 0
            )

            direction = (
                "improved"
                if change > 0
                else "decreased"
            )

            return (
                f"Your quiz performance {direction} "
                f"by {abs(change):.1f} percentage points."
            )

        # --------------------------------------------------
        # ASSIGNMENT PERFORMANCE
        # --------------------------------------------------

        if event.event_type == "assignment_performance_changed":

            change = (
                event.metadata.get("change", 0)
                if event.metadata
                else 0
            )

            direction = (
                "improved"
                if change > 0
                else "decreased"
            )

            return (
                f"Your assignment performance {direction} "
                f"by {abs(change):.1f} percentage points."
            )

        # --------------------------------------------------
        # QUIZ COMPLETED
        # --------------------------------------------------

        if event.event_type == "quiz_completed":

            return (
                f"You recently completed "
                f"'{event.title}'. Nice work."
            )

        # --------------------------------------------------
        # ASSIGNMENT SUBMITTED
        # --------------------------------------------------

        if event.event_type == "assignment_submitted":

            return (
                f"You recently submitted "
                f"'{event.title}'."
            )

        # --------------------------------------------------
        # OLD GRADE EVENT
        # --------------------------------------------------

        if event.event_type == "grade_changed":

            return (
                f"I noticed a grade update for "
                f"'{event.title}'."
            )

        # --------------------------------------------------
        # OVERDUE
        # --------------------------------------------------

        if event.event_type == "task_overdue":

            return (
                f"'{event.title}' became overdue. "
                f"Let's get it back on track."
            )

        # --------------------------------------------------
        # CLASSROOM REVISITED
        # --------------------------------------------------

        if event.event_type == "classroom_revisited":

            return (
                f"Welcome back to "
                f"{memory['classroom'].name}."
            )

        return None