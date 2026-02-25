from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CertificateRequest

User = get_user_model()


# ----------------------------
# Registration Form (UPDATED)
# ----------------------------
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'department']


# ----------------------------
# Certificate Request Form
# ----------------------------
class CertificateRequestForm(forms.ModelForm):
    class Meta:
        model = CertificateRequest
        fields = ['certificate_type', 'purpose']


# ----------------------------
# Login Form (Better Version)
# ----------------------------
class LoginForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
