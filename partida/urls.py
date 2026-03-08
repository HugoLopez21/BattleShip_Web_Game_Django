from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
app_name = 'partida'

urlpatterns = [
    path('nueva/', views.iniciar_partida, name='iniciar'),
    path('tablero/<int:partida_id>/', views.mostrar_partida, name='mostrar'),
    path('disparar/', views.recibe_disparo, name='disparo'),
    path('terminar/', views.abandonar_partida, name='abandonar'),
    path('turno_jugador/', views.turno_jugador, name='turno_jugador')
]
