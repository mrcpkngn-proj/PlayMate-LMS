from django import forms
from .models import Quiz, Question

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            "duration",
            "max_attempts",
            "display_mode",
            "use_question_timer",
            "shuffle_questions",
            "shuffle_choices",
        ]
        widgets = {
            "duration": forms.NumberInput(attrs={
                "class": "form-control retro-input",
                "min": 1
            }),
            "max_attempts": forms.NumberInput(attrs={
                "class": "form-control retro-input",
                "min": 1
            }),
            "display_mode": forms.RadioSelect(attrs={
                "class": "display-mode-option",
            }),
            "use_question_timer": forms.CheckboxInput(attrs={
                "id": "use-question-timer",
            }),
            "shuffle_questions": forms.CheckboxInput(),
            "shuffle_choices": forms.CheckboxInput(),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["duration", "text", "points", "answer_type"]
