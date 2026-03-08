from django.db import models
from admin_panel.models import Perfil



# Create your models here.
#MODELS APP INICIAL

class Reto(models.Model):
    retador = models.ForeignKey(Perfil, on_delete = models.CASCADE, related_name ='retador')
    retado = models.ForeignKey(Perfil, on_delete = models.CASCADE, related_name ='retado')
    estado = models.BooleanField( default =False)