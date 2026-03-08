from django.db import models
from django.contrib.auth.models import User

#MODELS APP PARTIDA

class Partida(models.Model):
    id = models.AutoField( primary_key = True)
    fecha = models.DateTimeField( auto_now_add = True)
    jugador1 = models.ForeignKey( User, on_delete = models.CASCADE, related_name = 'partidas_j1')
    jugador2 = models.ForeignKey( User, on_delete = models.CASCADE, related_name = 'partidas_j2')
    ganador = models.ForeignKey( User, on_delete = models.SET_NULL, null =True, blank =True)
    activa = models.BooleanField( default=True)


class DisposicionBarcos(models.Model):
    # Cada jugador tiene su tablero
    partida = models.ForeignKey( Partida, on_delete = models.CASCADE)
    jugador = models.ForeignKey( User, on_delete =models.CASCADE)
    tablero = models.JSONField()


class Ronda(models.Model):
    partida = models.ForeignKey(Partida, on_delete = models.CASCADE)
    numero = models.IntegerField()


class Turno(models.Model):
    ronda = models.ForeignKey( Ronda, on_delete = models.CASCADE)
    jugador_dispara = models.ForeignKey( User, on_delete = models.CASCADE)


class Disparo(models.Model):
    turno = models.OneToOneField(Turno,on_delete = models.CASCADE)
    coordenada = models.CharField( max_length=3)
    resultado = models.CharField( max_length=100, default= "Sin resultado")


class Barco(models.Model):
    partida = models.ForeignKey( Partida, on_delete = models.CASCADE)
    jugador = models.ForeignKey( User, on_delete = models.CASCADE)
    nombre = models.CharField( max_length = 20)
    tamaño = models.IntegerField()
    vida = models.IntegerField()
    hundido = models.BooleanField( default = False)
    posiciones = models.JSONField( default = list)