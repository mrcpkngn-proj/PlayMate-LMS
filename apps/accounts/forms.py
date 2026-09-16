from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserSettings


class RegisterForm(UserCreationForm):

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User

        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email

class ProfileForm(forms.ModelForm):

    email = forms.EmailField(required=True)

    class Meta:
        model = User

        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()

        if User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=self.instance.pk
        ).exists():

            raise forms.ValidationError(
                "This email is already being used by another account."
            )

        return email


class SettingsForm(forms.ModelForm):

    class Meta:

        model = UserSettings

        fields = (
            "classroom_notifications",
            "assignment_notifications",
            "quiz_notifications",
            "alec_companion",
            "alec_insights",
        )