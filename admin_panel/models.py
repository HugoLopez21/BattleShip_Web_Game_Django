from django.db import models
from django.contrib.auth.models import User

#Extiende de User 
class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete = models.CASCADE, related_name='perfil')
    nombre = models.CharField(max_length = 60, default="")
    apellido = models.CharField(max_length =50, default="")
    foto_perfil = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)
    partidas_ganadas = models.IntegerField(default = 0)
    partidas_perdidas = models.IntegerField(default =0)
    partidas_abandonadas = models.IntegerField(default = 0)
    buscando_partida = models.BooleanField(default = False)
    ultima_actividad = models.DateTimeField(auto_now = True)