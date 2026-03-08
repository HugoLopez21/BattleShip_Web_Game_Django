from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
app_name = 'inicial'

urlpatterns = [
    path('', auth_views.LoginView.as_view(), name='login'),
    path('', include('django.contrib.auth.urls')),
    path('home/', views.home, name='home'),
    path('lobby/', views.lobby, name='lobby'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('lobby_check/', views.buscando_contrincante, name='lobby_check'),
    path('retar/', views.retar_usuario, name = 'retar'),
    

]