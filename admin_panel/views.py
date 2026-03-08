from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import FormularioAlta, FormularioEditar
from django.contrib.auth.decorators import user_passes_test
from .models import Perfil
from partida.models import Partida, Ronda, Turno, Disparo, Barco, DisposicionBarcos
from django.http import HttpResponse
import json
from django.core import serializers



def es_admin(user):
    #Verifica que el usuario es administrador
    return user.is_superuser


#Unicamente entra si es administrador
@user_passes_test(es_admin)
def panel_principal(request):
    # Muestra el formulario de alta y la lista de usuarios
    # Dar de alta
    if request.method == 'POST':
        form = FormularioAlta(request.POST)
        if form.is_valid():
            #Guardar la informacion en la base de datos
            nuevo_user = form.save()
            Perfil.objects.create(
                usuario = nuevo_user,
                nombre = nuevo_user.first_name,
                apellido = nuevo_user.last_name,         
            )
            return redirect('admin_panel:panel_principal')
    else:
        form = FormularioAlta()

    # Mostrar listado de usuarios
    usuarios = User.objects.all().order_by('id')
    partidas = Partida.objects.all().order_by('-fecha').filter(activa = "False")
    return render(request, 'admin_panel/panel_administrador.html', {
        'form': form, 
        'usuarios': usuarios,
        'partidas': partidas
    })


def eliminar_usuario(request, user_id):
    # Dar de baja
    usuario = User.objects.get(id =user_id)
    
    if not usuario.is_superuser:
        usuario.delete() 
        messages.success(request, "Usuario eliminado")
    else:
        messages.error(request, "No puedes eliminar al administrador principal")
        
    return redirect('admin_panel:panel_principal')


def editar_usuario(request, user_id):
    # Modificar usuario
    usuario = User.objects.get(id = user_id)
    
    if request.method == 'POST':
        form = FormularioEditar(request.POST, instance = usuario)
        if form.is_valid():
            form.save()
            return redirect('admin_panel:panel_principal')
    else:
        # Llena los datos con los datos actuales
        form = FormularioEditar(instance = usuario)

    return render(request, 'admin_panel/editar.html', {'form': form, 'usuario': usuario})



def descargar_lista_usuarios(request):
    nombre_archivo = 'Lista_usuarios'
    usuarios = list(Perfil.objects.exclude(id=2).values('usuario', 'nombre', 'apellido', 'partidas_ganadas', 'partidas_perdidas', 'partidas_abandonadas'))
    return descargar(request, usuarios, nombre_archivo)


def descargar_partida(request):
    if request.method == 'POST':
        id_partida = request.POST.get('partida_id')
        nombre_archivo = f'Partida{id_partida}'
        
        try:
            partida_bd = Partida.objects.get(id=id_partida)
            
    
            data_partida = {
                'id' : partida_bd.id,
                'fecha' : str(partida_bd.fecha),
                'jugador1' : partida_bd.jugador1.username,
                'jugador2' : partida_bd.jugador2.username,
                'ganador' : partida_bd.ganador.username if partida_bd.ganador else None,
                'activa' : partida_bd.activa,
                'disposiciones': [],
                'barcos' : [],
                'rondas' : []
            }

            disposiciones = DisposicionBarcos.objects.filter(partida = partida_bd)
            for disp in disposiciones:
                data_partida['disposiciones'].append({
                    'jugador' : disp.jugador.username,
                    'tablero' : disp.tablero
                })

            barcos = Barco.objects.filter(partida = partida_bd)
            for b in barcos:
                data_partida['barcos'].append({
                    'jugador': b.jugador.username,
                    'nombre': b.nombre,
                    'tamaño': b.tamaño,
                    'posiciones' : b.posiciones,
                    'hundido' : b.hundido
                })

            # Rondas y Turnos
            rondas = Ronda.objects.filter(partida = partida_bd).order_by('numero')
            for r in rondas:
                data_ronda = {
                    'numero': r.numero,
                    'turnos': []
                }
                
                turnos = Turno.objects.filter(ronda = r).order_by('id')
                for t in turnos:
                    data_turno = {
                        'jugador': t.jugador_dispara.username,
                        'disparo': None
                    }
                    
                    try:
                        disparo = Disparo.objects.get(turno = t)
                        data_turno['disparo'] = {
                            'coordenada': disparo.coordenada,
                            'resultado': disparo.resultado
                        }
                    except Disparo.DoesNotExist:
                        pass
                        
                    data_ronda['turnos'].append(data_turno)
                
                data_partida['rondas'].append(data_ronda)

            return descargar(request, data_partida, nombre_archivo)
            
        except Partida.DoesNotExist:
            return HttpResponse("Partida no encontrada", status=404)


def descargar_ranking(request):
    nombre_archivo = 'Ranking'
    ranking = list(Perfil.objects.all().order_by('-partidas_ganadas').values('usuario', 'nombre','apellido','partidas_ganadas','partidas_perdidas','partidas_abandonadas'))
    return descargar(request, ranking, nombre_archivo)


def descargar(request, data, nombre_archivo):
    json_data = json.dumps(data, indent = 4, default = str)
    response = HttpResponse(json_data, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}.json"'
    return response