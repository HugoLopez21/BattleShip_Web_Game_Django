from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].error_messages = {
            'required': 'Debes introducir un usuario',
            'invalid': 'Usuario o contraseña incorrectos'
        }
        self.fields['password'].error_messages = {
            'required': 'Debes introducir una contraseña',
            'invalid': 'Usuario o contraseña incorrectos'
        }
        
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'forms',
            'placeholder': 'Usuario',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'forms',
            'placeholder': 'Contraseña'
        })
    )
