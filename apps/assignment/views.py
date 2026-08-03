from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction

from apps.classroom.models import Classroom, ClassroomMember, StreamPost
from apps.classroom.forms import ClassworkForm

from .models import Assignment, Submission, AssignmentAttachment
from .forms import AssignmentForm, SubmissionForm, SubmissionGradeForm



def user_can_access_assignment(user, assignment):

    classroom = assignment.classwork.classroom

    if user == classroom.teacher:
        return True

    return ClassroomMember.objects.filter(
        classroom=classroom,
        student=user,
    ).exists()


@login_required
def assignment_create(request, classroom_id):

    classroom = get_object_or_404(
        Classroom,
        pk=classroom_id,
        teacher=request.user,
    )

    if request.method == "POST":

        classwork_form = ClassworkForm(request.POST)
        assignment_form = AssignmentForm(request.POST)

        if classwork_form.is_valid() and assignment_form.is_valid():

            with transaction.atomic():

                classwork = classwork_form.save(commit=False)
                classwork.classroom = classroom
                classwork.work_type = "assignment"
                classwork.created_by = request.user
                classwork.save()

                assignment = assignment_form.save(commit=False)
                assignment.classwork = classwork
                assignment.save()

                files = request.FILES.getlist("attachments")

                for file in files:
                    AssignmentAttachment.objects.create(
                        assignment=assignment,
                        file=file,
                    )

            return redirect(
                "classroom:classroom_classwork",
                pk=classroom.id,
            )

    else:

        classwork_form = ClassworkForm()
        assignment_form = AssignmentForm()

    return render(
        request,
        "assignment/assignment_form.html",
        {
            "classroom": classroom,
            "classwork_form": classwork_form,
            "assignment_form": assignment_form,
        },
    )


@login_required
def assignment_update(request, assignment_id):

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
    )

    if not user_can_access_assignment(request.user, assignment):
        return redirect("classroom:classroom_list")

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
    )

    classroom = assignment.classwork.classroom

    if classroom.teacher != request.user:
        return redirect("classroom:classroom_list")

    if request.method == "POST":

        classwork_form = ClassworkForm(
            request.POST,
            instance=assignment.classwork,
        )

        assignment_form = AssignmentForm(
            request.POST,
            instance=assignment,
        )

        files = request.FILES.getlist("attachments")

        if classwork_form.is_valid() and assignment_form.is_valid():

            with transaction.atomic():

                classwork_form.save()
                assignment_form.save()

                for file in files:
                    AssignmentAttachment.objects.create(
                        assignment=assignment,
                        file=file,
                    )

            return redirect(
                "classroom:classroom_classwork",
                pk=classroom.id,
            )

    else:

        classwork_form = ClassworkForm(
            instance=assignment.classwork,
        )

        assignment_form = AssignmentForm(
            instance=assignment,
        )

    return render(
        request,
        "assignment/assignment_form.html",
        {
            "assignment": assignment,
            "classroom": classroom,
            "classwork_form": classwork_form,
            "assignment_form": assignment_form,
        },
    )


@login_required
def assignment_delete(request, assignment_id):

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
    )

    if not user_can_access_assignment(request.user, assignment):
        return redirect("classroom:classroom_list")

    classroom = assignment.classwork.classroom

    if classroom.teacher != request.user:
        return redirect("classroom:classroom_list")

    if request.method == "POST":

        assignment.classwork.delete()

        return redirect(
            "classroom:classroom_classwork",
            pk=classroom.id,
        )

    return render(
        request,
        "assignment/assignment_confirm_delete.html",
        {
            "assignment": assignment,
        },
    )

@login_required
def assignment_detail(request, assignment_id):

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
    )

    if not user_can_access_assignment(request.user, assignment):
        return redirect("classroom:classroom_list")

    classroom = assignment.classwork.classroom

    submission = Submission.objects.filter(
        assignment=assignment,
        student=request.user,
    ).first()

    if request.method == "POST" and request.user != classroom.teacher:

        if submission:
            return redirect(
                "assignment:assignment_detail",
                assignment_id=assignment.id,
            )

        form = SubmissionForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            new_submission = form.save(commit=False)
            new_submission.assignment = assignment
            new_submission.student = request.user
            new_submission.save()

            return redirect(
                "assignment:assignment_detail",
                assignment_id=assignment.id,
            )

    else:
        form = SubmissionForm()

    return render(
        request,
        "assignment/assignment_detail.html",
        {
            "assignment": assignment,
            "classroom": classroom,
            "submission": submission,
            "submission_form": form,
        },
    )


@login_required
def attachment_delete(request, attachment_id):

    attachment = get_object_or_404(
        AssignmentAttachment,
        id=attachment_id,
    )

    assignment = attachment.assignment

    classroom = assignment.classwork.classroom

    if request.user != classroom.teacher:
        return redirect("classroom:classroom_list")

    attachment.delete()

    return redirect(
        "assignment:assignment_update",
        assignment_id=assignment.id,
    )


@login_required
def submission_list(request, assignment_id):

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
    )

    classroom = assignment.classwork.classroom

    if request.user != classroom.teacher:
        return redirect(
            "assignment:assignment_detail",
            assignment.id,
        )

    submissions = (
        Submission.objects
        .filter(assignment=assignment)
        .select_related("student")
        .order_by("-submitted_at")
    )

    return render(
        request,
        "assignment/submission_list.html",
        {
            "assignment": assignment,
            "classroom": classroom,
            "submissions": submissions,
        },
    )


@login_required
def grade_submission(request, submission_id):

    submission = get_object_or_404(
        Submission,
        id=submission_id,
    )

    assignment = submission.assignment
    classroom = assignment.classwork.classroom

    if request.user != classroom.teacher:
        return redirect("classroom:classroom_list")

    if request.method == "POST":

        form = SubmissionGradeForm(
            request.POST,
            instance=submission,
            assignment=assignment,
        )

        if form.is_valid():

            form.save()

            return redirect(
                "assignment:submission_list",
                assignment.id,
            )

    else:

        form = SubmissionGradeForm(
            instance=submission,
            assignment=assignment,
        )

    return render(
        request,
        "assignment/grade_submission.html",
        {
            "submission": submission,
            "assignment": assignment,
            "classroom": classroom,
            "form": form,
        },
    )

