from django.utils import timezone

from .models import (
    AlecMemorySnapshot,
    AlecMemoryEvent,
)


class AlecMemory:

    """
    =========================================================
    A.L.E.C. Memory System
    =========================================================

    Working Memory:
        Information generated during the current request.

    Episodic Memory:
        Persistent events representing things that happened
        to the student.

    Snapshot Memory:
        Persistent snapshots representing the student's
        state at a particular point in time.

    Snapshot flow:

        Current State
              ↓
        Previous Snapshot
              ↓
        detect_changes()
              ↓
        save_snapshot()
              ↓
        create_change_events()
              ↓
        Recent Events
    """

    # ==================================================
    # BUILD MEMORY
    # ==================================================

    def build(
        self,
        student,
        classroom,
        report,
        task_list,
    ):
        """
        Build A.L.E.C.'s current memory.

        Change detection is performed against the previous
        snapshot.

        Important:
        The current snapshot is NOT treated as the previous
        snapshot until after changes have been calculated.
        """

        # --------------------------------------------------
        # TASK GROUPING
        # --------------------------------------------------

        overdue = [
            task
            for task in task_list
            if task["status"] == "overdue"
        ]

        today = [
            task
            for task in task_list
            if task["status"] == "today"
        ]

        upcoming = [
            task
            for task in task_list
            if task["status"] == "upcoming"
        ]

        # --------------------------------------------------
        # PERFORMANCE
        # --------------------------------------------------

        performance = report["performance"]

        # --------------------------------------------------
        # PRIORITY / AREAS
        # --------------------------------------------------

        priority = self.get_priority(
            task_list
        )

        strongest_area = self.get_strongest_area(
            performance
        )

        weakest_area = self.get_weakest_area(
            performance
        )

        # --------------------------------------------------
        # PREVIOUS SNAPSHOT
        # --------------------------------------------------

        previous = self.get_previous_snapshot(
            student,
            classroom,
        )

        # --------------------------------------------------
        # CURRENT STATE
        # --------------------------------------------------

        current = {
            "overall_average":
                performance["overall_average"],

            "quiz_average":
                performance["quiz_average"],

            "assignment_average":
                performance["assignment_average"],

            "completed_quizzes":
                performance["completed_quizzes"],

            "graded_assignments":
                performance["graded_assignments"],

            "overdue_count":
                len(overdue),

            "total_task_count":
                len(task_list),
        }

        # --------------------------------------------------
        # DETECT CHANGES
        # --------------------------------------------------
        #
        # IMPORTANT:
        # This happens BEFORE saving the current snapshot.
        #
        # Therefore:
        #
        # previous = old state
        # current  = new state
        #
        # Example:
        #
        # previous overall = 91.9
        # current overall  = 98.6
        #
        # overall_change = +6.7
        #
        # --------------------------------------------------

        changes = self.detect_changes(
            current,
            previous,
        )

        # --------------------------------------------------
        # SAVE SNAPSHOT
        # --------------------------------------------------
        #
        # save_snapshot() returns the existing snapshot if
        # nothing actually changed.
        #
        # Otherwise it creates a new baseline snapshot.
        #
        # --------------------------------------------------

        snapshot = self.save_snapshot(
            student,
            classroom,
            current,
        )

        # --------------------------------------------------
        # CREATE CHANGE EVENTS
        # --------------------------------------------------
        #
        # This is the ONLY place where performance-change
        # events are generated.
        #
        # Do NOT call another change-event method.
        #
        # --------------------------------------------------

        self.create_change_events(
            student=student,
            classroom=classroom,
            changes=changes,
            snapshot=snapshot,
            previous=previous,
        )

        # --------------------------------------------------
        # RECENT EVENTS
        # --------------------------------------------------

        recent_events = self.get_recent_events(
            student,
            classroom,
        )

        # --------------------------------------------------
        # COMPLETE MEMORY
        # --------------------------------------------------

        memory = {

            "student":
                student,

            "classroom":
                classroom,

            "performance":
                performance,

            "progress":
                report["progress"],

            "risk":
                report["risk"],

            "overdue":
                overdue,

            "today":
                today,

            "upcoming":
                upcoming,

            "priority":
                priority,

            "strongest_area":
                strongest_area,

            "weakest_area":
                weakest_area,

            "overall_level":
                report["level"],

            "changes":
                changes,

            "previous_snapshot":
                previous,

            "current_snapshot":
                snapshot,

            "time":
                timezone.localtime(),

            "recent_events":
                recent_events,
        }

        return memory

    # ==================================================
    # PREVIOUS SNAPSHOT
    # ==================================================

    def get_previous_snapshot(
        self,
        student,
        classroom,
    ):
        """
        Get the most recent snapshot.
        """

        return (
            AlecMemorySnapshot.objects
            .filter(
                student=student,
                classroom=classroom,
            )
            .order_by("-created_at")
            .first()
        )

    # ==================================================
    # CHANGE DETECTION
    # ==================================================

    def detect_changes(
        self,
        current,
        previous,
    ):
        """
        Compare the current state with the previous
        snapshot.

        This method is the SINGLE SOURCE OF TRUTH for
        detecting changes.

        Returns:

            overall_change
            quiz_change
            assignment_change
            overdue_change
            task_count_change
            completed_quizzes_change
            graded_assignments_change
        """

        # --------------------------------------------------
        # FIRST VISIT
        # --------------------------------------------------

        if not previous:

            return {
                "is_first_visit": True,

                "overall_change": 0,

                "quiz_change": 0,

                "assignment_change": 0,

                "overdue_change": 0,

                "task_count_change": 0,

                "completed_quizzes_change": 0,

                "graded_assignments_change": 0,
            }

        # --------------------------------------------------
        # EXISTING STUDENT
        # --------------------------------------------------

        return {

            "is_first_visit": False,

            # ----------------------------------------------
            # PERFORMANCE
            # ----------------------------------------------

            "overall_change":
                current["overall_average"]
                - previous.overall_average,

            "quiz_change":
                current["quiz_average"]
                - previous.quiz_average,

            "assignment_change":
                current["assignment_average"]
                - previous.assignment_average,

            # ----------------------------------------------
            # TASKS
            # ----------------------------------------------

            "overdue_change":
                current["overdue_count"]
                - previous.overdue_count,

            "task_count_change":
                current["total_task_count"]
                - previous.total_task_count,

            # ----------------------------------------------
            # COMPLETION
            # ----------------------------------------------

            "completed_quizzes_change":
                current["completed_quizzes"]
                - previous.completed_quizzes,

            "graded_assignments_change":
                current["graded_assignments"]
                - previous.graded_assignments,
        }

    # ==================================================
    # CHANGE EVENTS
    # ==================================================

    def create_change_events(
        self,
        student,
        classroom,
        changes,
        snapshot,
        previous,
    ):
        """
        Convert detected changes into episodic memory.

        THIS IS THE ONLY METHOD responsible for creating
        automatic performance/state change events.

        Events are tied to the NEW snapshot ID.

        Therefore refreshing the dashboard does not create
        duplicate events for the same snapshot.
        """

        # --------------------------------------------------
        # FIRST VISIT
        # --------------------------------------------------

        if changes.get("is_first_visit"):
            return

        snapshot_id = snapshot.id

        # --------------------------------------------------
        # EXTRACT CHANGES
        # --------------------------------------------------

        overall_change = changes.get(
            "overall_change",
            0,
        )

        quiz_change = changes.get(
            "quiz_change",
            0,
        )

        assignment_change = changes.get(
            "assignment_change",
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

        # ==================================================
        # OVERALL PERFORMANCE
        # ==================================================

        if overall_change >= 3:

            self.record_change_event(
                student=student,
                classroom=classroom,
                event_type="performance_improved",
                title="Overall performance improved",
                description=(
                    "Your overall performance "
                    f"increased by "
                    f"{overall_change:.1f} percentage "
                    "points."
                ),
                snapshot_id=snapshot_id,
                metadata={
                    "area": "overall",
                    "change": round(
                        overall_change,
                        2,
                    ),
                    "direction": "increase",
                },
            )

        elif overall_change <= -5:

            self.record_change_event(
                student=student,
                classroom=classroom,
                event_type="performance_declined",
                title="Overall performance declined",
                description=(
                    "Your overall performance "
                    f"decreased by "
                    f"{abs(overall_change):.1f} "
                    "percentage points."
                ),
                snapshot_id=snapshot_id,
                metadata={
                    "area": "overall",
                    "change": round(
                        overall_change,
                        2,
                    ),
                    "direction": "decrease",
                },
            )

        # ==================================================
        # QUIZ PERFORMANCE
        # ==================================================

        if abs(quiz_change) >= 5:

            if quiz_change > 0:

                title = "Quiz performance improved"

                description = (
                    "Your quiz performance "
                    f"increased by "
                    f"{quiz_change:.1f} percentage "
                    "points."
                )

                direction = "increase"

            else:

                title = "Quiz performance declined"

                description = (
                    "Your quiz performance "
                    f"decreased by "
                    f"{abs(quiz_change):.1f} "
                    "percentage points."
                )

                direction = "decrease"

            self.record_change_event(
                student=student,
                classroom=classroom,
                event_type="quiz_performance_changed",
                title=title,
                description=description,
                snapshot_id=snapshot_id,
                metadata={
                    "area": "quiz",
                    "change": round(
                        quiz_change,
                        2,
                    ),
                    "direction": direction,
                },
            )

        # ==================================================
        # ASSIGNMENT PERFORMANCE
        # ==================================================

        if abs(assignment_change) >= 5:

            if assignment_change > 0:

                title = (
                    "Assignment performance improved"
                )

                description = (
                    "Your assignment performance "
                    f"increased by "
                    f"{assignment_change:.1f} "
                    "percentage points."
                )

                direction = "increase"

            else:

                title = (
                    "Assignment performance declined"
                )

                description = (
                    "Your assignment performance "
                    f"decreased by "
                    f"{abs(assignment_change):.1f} "
                    "percentage points."
                )

                direction = "decrease"

            self.record_change_event(
                student=student,
                classroom=classroom,
                event_type=(
                    "assignment_performance_changed"
                ),
                title=title,
                description=description,
                snapshot_id=snapshot_id,
                metadata={
                    "area": "assignment",
                    "change": round(
                        assignment_change,
                        2,
                    ),
                    "direction": direction,
                },
            )

        # ==================================================
        # QUIZ COMPLETION
        # ==================================================

        if completed_quizzes_change > 0:

            self.record_change_event(
                student=student,
                classroom=classroom,
                event_type="quiz_progress",
                title="Quiz progress increased",
                description=(
                    "You completed "
                    f"{completed_quizzes_change} "
                    "additional quiz"
                    f"{'zes' if completed_quizzes_change != 1 else ''}."
                ),
                snapshot_id=snapshot_id,
                metadata={
                    "area": "quiz_completion",
                    "change":
                        completed_quizzes_change,
                    "direction": "increase",
                },
            )

        # ==================================================
        # ASSIGNMENT COMPLETION / GRADING
        # ==================================================

        if graded_assignments_change > 0:

            self.record_change_event(
                student=student,
                classroom=classroom,
                event_type="assignment_progress",
                title="Assignment progress increased",
                description=(
                    "You completed "
                    f"{graded_assignments_change} "
                    "additional assignment"
                    f"{'s' if graded_assignments_change != 1 else ''}."
                ),
                snapshot_id=snapshot_id,
                metadata={
                    "area": "assignment_completion",
                    "change":
                        graded_assignments_change,
                    "direction": "increase",
                },
            )

        # ==================================================
        # OVERDUE TASKS
        # ==================================================

        if overdue_change > 0:

            self.record_change_event(
                student=student,
                classroom=classroom,
                event_type="task_overdue",
                title="Overdue tasks increased",
                description=(
                    "You now have "
                    f"{overdue_change} more overdue "
                    "task"
                    f"{'s' if overdue_change != 1 else ''}."
                ),
                snapshot_id=snapshot_id,
                metadata={
                    "area": "overdue_tasks",
                    "change": overdue_change,
                    "direction": "increase",
                },
            )

        # ==================================================
        # OVERDUE TASKS REDUCED
        # ==================================================

        elif overdue_change < 0:

            self.record_change_event(
                student=student,
                classroom=classroom,
                event_type="task_overdue_reduced",
                title="Overdue tasks reduced",
                description=(
                    "You reduced your overdue tasks "
                    f"by {abs(overdue_change)} "
                    "task"
                    f"{'s' if abs(overdue_change) != 1 else ''}."
                ),
                snapshot_id=snapshot_id,
                metadata={
                    "area": "overdue_tasks",
                    "change": overdue_change,
                    "direction": "decrease",
                },
            )

    # ==================================================
    # RECORD CHANGE EVENT
    # ==================================================

    def record_change_event(
        self,
        student,
        classroom,
        event_type,
        title,
        description,
        snapshot_id,
        metadata=None,
    ):
        """
        Record a change event exactly once.

        The snapshot ID is the unique source of the event.

        If the dashboard is refreshed, the same snapshot is
        found again and the event is NOT recreated.
        """

        if metadata is None:
            metadata = {}

        metadata = {
            **metadata,
            "snapshot_id": snapshot_id,
        }

        existing = (
            AlecMemoryEvent.objects
            .filter(
                student=student,
                classroom=classroom,
                event_type=event_type,
                metadata__snapshot_id=snapshot_id,
            )
            .first()
        )

        if existing:
            return existing

        return AlecMemoryEvent.objects.create(
            student=student,
            classroom=classroom,
            event_type=event_type,
            title=title,
            description=description,
            metadata=metadata,
        )

    # ==================================================
    # SAVE SNAPSHOT
    # ==================================================

    def save_snapshot(
        self,
        student,
        classroom,
        current,
    ):
        """
        Save a new snapshot only when the student's state
        has actually changed.

        If nothing changed, return the existing snapshot.
        """

        latest = (
            AlecMemorySnapshot.objects
            .filter(
                student=student,
                classroom=classroom,
            )
            .order_by("-created_at")
            .first()
        )

        # --------------------------------------------------
        # NO PREVIOUS SNAPSHOT
        # --------------------------------------------------

        if not latest:

            return AlecMemorySnapshot.objects.create(
                student=student,
                classroom=classroom,

                overall_average=
                    current["overall_average"],

                quiz_average=
                    current["quiz_average"],

                assignment_average=
                    current["assignment_average"],

                completed_quizzes=
                    current["completed_quizzes"],

                graded_assignments=
                    current["graded_assignments"],

                overdue_count=
                    current["overdue_count"],

                total_task_count=
                    current["total_task_count"],
            )

        # --------------------------------------------------
        # CHECK WHETHER STATE CHANGED
        # --------------------------------------------------

        unchanged = (

            latest.overall_average
            == current["overall_average"]

            and

            latest.quiz_average
            == current["quiz_average"]

            and

            latest.assignment_average
            == current["assignment_average"]

            and

            latest.completed_quizzes
            == current["completed_quizzes"]

            and

            latest.graded_assignments
            == current["graded_assignments"]

            and

            latest.overdue_count
            == current["overdue_count"]

            and

            latest.total_task_count
            == current["total_task_count"]
        )

        if unchanged:
            return latest

        # --------------------------------------------------
        # CREATE NEW SNAPSHOT
        # --------------------------------------------------

        return AlecMemorySnapshot.objects.create(
            student=student,
            classroom=classroom,

            overall_average=
                current["overall_average"],

            quiz_average=
                current["quiz_average"],

            assignment_average=
                current["assignment_average"],

            completed_quizzes=
                current["completed_quizzes"],

            graded_assignments=
                current["graded_assignments"],

            overdue_count=
                current["overdue_count"],

            total_task_count=
                current["total_task_count"],
        )

    # ==================================================
    # RECORD EVENT
    # ==================================================

    def record_event(
        self,
        student,
        classroom,
        event_type,
        title="",
        description="",
        metadata=None,
    ):
        """
        Record an episodic event.

        Used for events that are not automatically generated
        from snapshot changes, such as quiz completion.
        """

        if metadata is None:
            metadata = {}

        # --------------------------------------------------
        # PREVENT DUPLICATE QUIZ EVENTS
        # --------------------------------------------------

        if event_type == "quiz_completed":

            attempt_id = metadata.get(
                "attempt_id"
            )

            if attempt_id:

                existing = (
                    AlecMemoryEvent.objects
                    .filter(
                        student=student,
                        classroom=classroom,
                        event_type=event_type,
                        metadata__attempt_id=attempt_id,
                    )
                    .first()
                )

                if existing:
                    return existing

        # --------------------------------------------------
        # CREATE EVENT
        # --------------------------------------------------

        return AlecMemoryEvent.objects.create(
            student=student,
            classroom=classroom,
            event_type=event_type,
            title=title,
            description=description,
            metadata=metadata,
        )

    # ==================================================
    # RECENT EVENTS
    # ==================================================

    def get_recent_events(
        self,
        student,
        classroom,
        limit=5,
    ):
        """
        Return recent unacknowledged episodic events.
        """

        return list(
            AlecMemoryEvent.objects
            .filter(
                student=student,
                classroom=classroom,
                acknowledged=False,
            )
            .order_by(
                "-created_at"
            )[:limit]
        )

    # ==================================================
    # ACKNOWLEDGE EVENT
    # ==================================================

    def acknowledge_event(
        self,
        event,
    ):
        """
        Mark an episodic event as acknowledged.
        """

        event.acknowledged = True

        event.save(
            update_fields=[
                "acknowledged"
            ]
        )

    # ==================================================
    # PRIORITY
    # ==================================================

    def get_priority(
        self,
        task_list,
    ):
        """
        Determine the highest-priority task.

        Priority:

            1. Overdue
            2. Due today
            3. Upcoming
        """

        for status in (
            "overdue",
            "today",
            "upcoming",
        ):

            for task in task_list:

                if task["status"] == status:

                    return {
                        "title":
                            task["title"],

                        "type":
                            task["type"],

                        "status":
                            status,

                        "reason":
                            self.get_reason(
                                status
                            ),

                        "urgency":
                            self.get_urgency(
                                status
                            ),

                        "message":
                            self.get_message(
                                status
                            ),
                    }

        return None

    # ==================================================
    # PRIORITY REASON
    # ==================================================

    def get_reason(
        self,
        status,
    ):
        reasons = {

            "overdue":
                "This task is overdue.",

            "today":
                "This task is due today.",

            "upcoming":
                "This is your next scheduled activity.",
        }

        return reasons.get(
            status,
            "",
        )

    # ==================================================
    # PRIORITY URGENCY
    # ==================================================

    def get_urgency(
        self,
        status,
    ):
        urgency = {

            "overdue":
                "critical",

            "today":
                "high",

            "upcoming":
                "normal",
        }

        return urgency.get(
            status,
            "normal",
        )

    # ==================================================
    # PRIORITY MESSAGE
    # ==================================================

    def get_message(
        self,
        status,
    ):
        messages = {

            "overdue":
                "Complete this before anything else.",

            "today":
                "Finish this today to stay on track.",

            "upcoming":
                "Prepare for this activity next.",
        }

        return messages.get(
            status,
            "",
        )

    # ==================================================
    # STRONGEST AREA
    # ==================================================

    def get_strongest_area(
        self,
        performance,
    ):
        """
        Determine whether quizzes or assignments
        are currently the student's strongest area.
        """

        if (
            performance["quiz_average"]
            >
            performance["assignment_average"]
        ):

            return "quizzes"

        if (
            performance["assignment_average"]
            >
            performance["quiz_average"]
        ):

            return "assignments"

        return "balanced"

    # ==================================================
    # WEAKEST AREA
    # ==================================================

    def get_weakest_area(
        self,
        performance,
    ):
        """
        Determine whether quizzes or assignments
        are currently the student's weakest area.
        """

        if (
            performance["quiz_average"]
            <
            performance["assignment_average"]
        ):

            return "quizzes"

        if (
            performance["assignment_average"]
            <
            performance["quiz_average"]
        ):

            return "assignments"

        return None