from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

# Formulario para dar de altacontraseña
class FormularioAlta(UserCreationForm):    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',]
        labels = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
        }

# Formulario para modificar usuario
class FormularioEditar(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',]