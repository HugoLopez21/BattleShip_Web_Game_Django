from urllib import request
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import LoginForm
from django.contrib.auth import authenticate, login as auth_login
from admin_panel.models import Perfil, User
from .models import Reto
from partida.models import Partida
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
import json

# Create your views here.


@login_required
def home(request):
    # Si el usaurio que inici sesion es el admin le redirige al panel admin
    if request.user.is_superuser:
        return redirect('admin_panel:panel_principal') 
    iniciar_sesion(request)
    
    ranking = load_ranking()
    return render(request, 'inicial/home.html', {'ranking': ranking})

def load_ranking():
    return Perfil.objects.all().order_by('-partidas_ganadas').exclude(usuario__username="Cpu")

@login_required
def cerrar_sesion(request):
    borrar_sesion(request)
    return redirect('inicial:login')

@login_required
def lobby(request):
    perfil_propio = request.user.perfil
    perfil_propio.buscando_partida = True
    perfil_propio.save() 


    limite = timezone.now() - timedelta(minutes = 2)

    Perfil.objects.filter(
        buscando_partida = True, 
        ultima_actividad__lt = limite
    ).update(buscando_partida=False)

    # Lista a los usarios que hayan entrado a lobby ya que estan buscando partida
    usuarios_activos = Perfil.objects.filter(buscando_partida = True).exclude(usuario = request.user)
    return render(request, 'inicial/lobby.html', {'usuarios_activos': usuarios_activos})

def refrescar_sesion(request):
    # Reinicia el tiempo de la variable de sesión cundo se llame
    try:
        request.session.set_expiry(600)
        print('Tiempo de sesion reinciado')
        return HttpResponse('ok')

    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'mensaje': f'Error interno: {str(e)}'
        })


def verificar_sesion(request):
    #Comprueba si la sesion sigue activa o no
    activa = request.session.get('sesion_activa', False)
    
    print(f'sesion: {activa}')
    return JsonResponse({'estado_sesion': activa})

def iniciar_sesion(request):
    # Crea la variable de sesion con un tiempo de 10 mins
    try:
        request.session.set_expiry(600)  #10 minutos
        request.session['sesion_activa'] = True
        
        print('Sesíon activada')
        return JsonResponse({
            'status': 'ok', 
            'mensaje': 'Sesión de 10 minutos iniciada.'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'mensaje': f'Error interno: {str(e)}'
        })
    
def borrar_sesion(request):
    #Borra la sesion y envia mensaje de estado
    try:
        request.session.flush()
        print(f'Sesión borrada')
        return JsonResponse({
            'status': 'ok', 
            'mensaje': 'Sesión cerrada'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'mensaje': f'Error interno: {str(e)}'
        })


@login_required
def retar_usuario(request):
    try:
        if request.method == 'POST':
            
            #Obtener el id del jugador a retar mediante el body del post
            data = json.loads(request.body)
            retado_id = data.get('retado_id')
            
            #Buscar en la base de datos los usarios
            retador = Perfil.objects.get(usuario = request.user)
            retado = Perfil.objects.get(id = retado_id)

            #Limpiar retos anteriores
            Reto.objects.filter(retador=retador, estado=  False).delete()
            reto = Reto.objects.create(retador = retador, retado = retado)

            #Crear el reto en la variable de sesion
            request.session['mi_reto'] = reto.id

            #Crear tabla con cada usuario para identificar cual es el retado y cua lel retador
            return JsonResponse({'mensaje': f'Esperando respuesta de {retado.usuario.username}'})
            
    except Exception as e:
        return JsonResponse({"Error": str(e)}, status=400)
    
@login_required
def buscando_contrincante(request):
    try:
        #Acceder a la variable de sesion
        mi_reto = request.session.get('mi_reto')
        retado = Perfil.objects.get(usuario = request.user)
        reto = Reto.objects.filter(retado = retado, estado =False).last()
        
        # Comprobar que el jugador no se reta asi mismo
        if reto and mi_reto != reto.id:
            reto.estado = True
            reto.save()
            retador = reto.retador.usuario

            #Devuelve el estado del reto, mensaje y el id del retador
            return JsonResponse({
                'retado': True, 
                'mensaje': f'¿Quieres aceptar el reto de {retador.username}?',
                'id_retador': retador.id
            })
        else:
            # Verificar si el reto fue aceptado
            if mi_reto:
                reto_propio = Reto.objects.filter(id=mi_reto, estado=True).first()
                if reto_propio:
                    # Buscar la partida abierta más reciente con el usuario
                    partida_reciente = Partida.objects.filter(
                        #El usuario puede ser el jugador 1 o 2
                        Q(jugador1 =request.user ) | Q(jugador2 = request.user)
                    ).order_by('-id').first()
                    if partida_reciente:
                        return JsonResponse({
                            'partida_iniciada': True,
                            'partida_id': partida_reciente.id
                        })
            return JsonResponse({'retado': False})    
    
    except Exception as e:
        return JsonResponse({"Error": str(e)}, status=400)