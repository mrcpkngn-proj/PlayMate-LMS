from django import forms
from .models import Classroom, Classwork, StreamPost


class ClassroomForm(forms.ModelForm):

    class Meta:
        model = Classroom

        fields = [
            "name",
            "description",
            "section",
            "cover_image",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "placeholder": "Classroom Name"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Description"
                }
            ),

            "section": forms.TextInput(
                attrs={
                    "placeholder": "Grade 1 - Adventurous"
                }
            ),

        }

class ClassworkForm(forms.ModelForm):

    class Meta:
        model = Classwork

        fields = [
            "title",
            "description",
            "due_date",
        ]

        widgets = {
            "due_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
        }


class AnnouncementForm(forms.ModelForm):

    class Meta:

        model = StreamPost

        fields = ["message"]

        widgets = {

            "message": forms.Textarea(

                attrs={

                    "rows": 3,

                    "placeholder": "Share something with your class..."

                }

            )

        }