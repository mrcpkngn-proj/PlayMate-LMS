from django import forms
from .models import Assignment, Submission


class AssignmentForm(forms.ModelForm):

    class Meta:

        model = Assignment

        fields = [
            "instructions",
            "points",
        ]

        
class SubmissionForm(forms.ModelForm):

    class Meta:

        model = Submission

        fields = [
            "submission_file",
        ]

        widgets = {

            "submission_file": forms.ClearableFileInput(
                attrs={
                    "class": "retro-input",
                }
            ),

        }


class SubmissionGradeForm(forms.ModelForm):

    class Meta:
        model = Submission

        fields = [
            "grade",
            "feedback",
        ]

        widgets = {
            "feedback": forms.Textarea(
                attrs={
                    "rows": 5,
                }
            ),
        }

    def __init__(self, *args, assignment=None, **kwargs):

        super().__init__(*args, **kwargs)

        if assignment:

            self.fields["grade"].widget.attrs.update({

                "min":0,

                "max":assignment.points,

            })

            self.assignment = assignment


    def clean_grade(self):

        grade = self.cleaned_data["grade"]

        if grade < 0:

            raise forms.ValidationError(
                "Grade cannot be negative."
            )

        if grade > self.assignment.points:

            raise forms.ValidationError(

                f"Grade cannot exceed {self.assignment.points}."

            )

        return grade