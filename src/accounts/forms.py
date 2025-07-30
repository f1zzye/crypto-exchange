from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm


User = get_user_model()


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(label=_("Username"), widget=forms.TextInput())
    email = forms.EmailField(label=_("E-mail"), widget=forms.EmailInput())
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput())
    password2 = forms.CharField(
        label=_("Confirm Password"), widget=forms.PasswordInput()
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
