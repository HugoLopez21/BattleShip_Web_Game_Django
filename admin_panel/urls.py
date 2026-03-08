from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.panel_principal, name='panel_principal'),
    path('eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('descargar_lista_usuarios/', views.descargar_lista_usuarios, name='descargar_lista_usuarios'),
    path('descargar_partida/', views.descargar_partida, name='descargar_partida'),
    path('descargar_ranking/', views.descargar_ranking, name='descargar_ranking'),

]