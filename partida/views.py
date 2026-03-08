import json
import random
import traceback
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from admin_panel.models import Perfil
from .models import Partida, DisposicionBarcos, Turno, Disparo, Ronda, Barco

SIZE = 8

# -------------- OBJETOS DE LA PARTIDA ------------------

class Sesion_partida:
    def __init__(self, jugador1, jugador2, partida_bd):
        self.partida_bd = partida_bd
        self.SIZE = SIZE
        self.jugador1 = jugador1
        self.jugador2 = jugador2
        self.turno = 1
        self.ronda = 1
        self.estado = True
        self.ganador = None
    
    # FUNCIONES QUE MONTAN LA PARTIDA --------------------------------------
    def crear_partida(self):
        """
        1. Genera tableros para cada jugador.
        2. Genera y posiciona barcos.
        3. Guarda la disposición en la base de datos.
        """
        self.jugador1.tablero = self.crear_tablero()
        barcos_j1 = self.generar_barcos(self.partida_bd.jugador1)
        self.asignar_todos_barcos(self.jugador1.tablero, barcos_j1)
        
        self.jugador2.tablero = self.crear_tablero()
        barcos_j2 = self.generar_barcos(self.partida_bd.jugador2)
        self.asignar_todos_barcos(self.jugador2.tablero, barcos_j2)
        
        # Almacenar en la bd las posiciones del jugador 1
        DisposicionBarcos.objects.create(
            partida=self.partida_bd,
            jugador=self.partida_bd.jugador1,
            tablero=self.jugador1.tablero
        )

        # Almacenar en la bd las posiciones del jugador 2
        DisposicionBarcos.objects.create(
            partida=self.partida_bd,
            jugador=self.partida_bd.jugador2,
            tablero=self.jugador2.tablero
        )
        print('Partida creada con éxito')

    def crear_tablero(self):
        # Crea un array de arrays o matriz con bordes para establecer el limite del tablero
        tablero = []
        for i in range(SIZE + 2):
            fila = []
            for j in range(SIZE + 2):
                #Añadir bordes
                if i == 0 or i == SIZE + 1 or j == 0 or j == SIZE + 1:
                    fila.append('B')

                # Lo demás agua
                else:
                    fila.append('A') 
            tablero.append(fila)
        return tablero

    def generar_barcos(self, jugador):
        '''
        1. Establece las propiedades de los barcos
        2. Por cada uno le asigna las propiedades segun el jugador
        '''
        configuracion_barcos = [
            (2, 4, 'Acorazado'),
            (2, 3, 'Submarino'),
            (3, 2, 'Destructor'),
            (4, 1, 'Patrullero'),
        ]
        
        barcos_creados = []
        for cantidad, tamaño, nombre in configuracion_barcos:
            for i in range(cantidad):
                barco = Barco.objects.create(
                    partida = self.partida_bd,
                    jugador = jugador,
                    tamaño = tamaño,
                    nombre = nombre,
                    vida = tamaño,
                    hundido = False
                )
                barcos_creados.append(barco)
        return barcos_creados

    def comprobar_espacio(self, tablero, fila, columna, BARCO_SIZE, EJE):
        '''
        Recibimos:
            - El tablero a comprobar
            - Las coordenad (fila, columna)
            - Tamaño del barco
            - La direccin de como se va a colocar

        Devuelve si cabe o no en un booleano
        '''
        # Comprueba si hay espacio para colocar el barco en el tablero
        for i in range(-1, BARCO_SIZE + 1):
            if EJE == 0:  # Horizontal
                col_revisar = columna + i 
                
                if (i == -1 or i == BARCO_SIZE):
                    filas_revisar = [fila]  
                else: 
                    filas_revisar = [fila - 1, fila, fila + 1]
                
                for f in filas_revisar:
                    celda = tablero[f][col_revisar]
                    # Falso si hay algo que no sea el borde o agua
                    if celda != 'A' and celda != 'B': 
                        return False
                    
            else:  # Vertical
                # Repite el proceso pero para el eje vertical
                fila_revisar = fila + i
                if (i == -1 or i == BARCO_SIZE):
                    cols_revisar = [columna]  
                else:
                    cols_revisar = [columna - 1, columna, columna + 1]
                
                for c in cols_revisar:
                    celda = tablero[fila_revisar][c]
                    if celda != 'A' and celda != 'B':
                        return False
        return True

    def colocar_barco(self, barco, tablero):
        '''
        La función coloca el barco en el tablero preguntado si cabe o no
        Tiene 100 intentos para colocar el barco
        '''
        intentos = 0
        while intentos < 100:
            EJE = random.randint(0, 1)
            if EJE == 0:  # Horizontal
                fila = random.randint(1, SIZE)
                columna = random.randint(1, SIZE - barco.tamaño + 1)
            else:  # Vertical
                fila = random.randint(1, SIZE - barco.tamaño + 1)
                columna = random.randint(1, SIZE)
                
            if self.comprobar_espacio(tablero, fila, columna, barco.tamaño, EJE):
                coordenadas_ocupadas = []
                
                # Actializa la posicion con el id del barco 
                for i in range(barco.tamaño):
                    if EJE == 0:
                        f, c = (fila, columna + i) 
                    else:
                        f, c = (fila + i, columna)
                    tablero[f][c] = barco.id
                    coordenadas_ocupadas.append([f, c])
                
                # Guarda las posiciones donde está el barco
                barco.posiciones = coordenadas_ocupadas
                barco.save()
                return True
            intentos += 1
        return False

    def asignar_todos_barcos(self, tablero, lista_barcos):
        for barco in lista_barcos:
            self.colocar_barco(barco, tablero)




    # FUNCIONES DE LA LOGICA DE LA PARTIDA --------------------------------------------------------------

    def ejecutar_turno(self, coordenadas):
        ronda_actual = Ronda.objects.get(partida = self.partida_bd , numero = self.ronda)
        
        if self.turno == 1:
            turno_bd = Turno.objects.create(ronda=ronda_actual, jugador_dispara=self.partida_bd.jugador1)
            self.cambiar_turno()
            return self.disparar(coordenadas, self.partida_bd.jugador2, turno_bd)
        
        else:
            turno_bd = Turno.objects.create(ronda=ronda_actual, jugador_dispara=self.partida_bd.jugador2)
            self.cambiar_turno()
            self.siguiente_ronda()
            return self.disparar(coordenadas, self.partida_bd.jugador1, turno_bd)

    
    def cambiar_turno(self):
        if self.turno == 1:
            self.turno = 2
        else:
            self.turno =  1

    def siguiente_ronda(self):
        self.ronda += 1
        #Busca la ronda que coincida con la partida actual y el numero actual
        Ronda.objects.create(partida = self.partida_bd, numero = self.ronda)

    def disparar(self, coordenadas, jugador_enemigo, turno_bd):
        '''
        1. Recibe las coordenadas donde se dispara, el jugador enemigo y el turno actual
        2. Se establecen las coordenadas como fila y columna
        3. Comprobamos si el disparo impacta en el tablero enemigo
            - Si impacta comprueba si se han hundido todos y es victoria
        5. Devuelve un diccionario con informacion del resultado
        '''
        fila = int(coordenadas['x'])
        columna = int(coordenadas['y'])
        
        #Obtener la disposicion de barcos del enemigp
        disposicion = DisposicionBarcos.objects.get(partida = self.partida_bd, jugador = jugador_enemigo)

        #Comprueba el resultado del disparo
        es_impacto = self.comprobar_casilla(columna, fila, disposicion)
        
        if es_impacto == "repetido":
            return {"estado": False, "mensaje": "No se puede volver a disparar aquí"}

        # Guardamos en la BD solo el string del estado, no el diccionario completo
        if isinstance(es_impacto, dict):
            resultado_bd = "hundido"
        else: 
            resultado_bd = str(es_impacto)
        
        #Crear el disparo ya heco con su resultado en la bd
        Disparo.objects.create( turno = turno_bd, coordenada = f'{columna},{fila}' , resultado = resultado_bd)

        # En caso de impacto se comprueba si ha ganado
        if es_impacto:
            es_victoria = self.comprobar_victoria(jugador_enemigo)
            
            # Si es victoria ponemos ganador y perdedor
            if es_victoria:
                ganador, perdedor = asignar_ganador_perdedor(jugador_enemigo, self.partida_bd)
                terminar_partida(self.partida_bd, ganador, perdedor)
                
                # El mensaje depende de quién ha disparado
                if isinstance(es_impacto, dict):
                    res_pos = es_impacto.get('posiciones')
                else:
                    res_pos = None

                return {
                    "estado": "hundido", 
                    "mensaje": f"¡VICTORIA! Se han hundido todos los barcos de {jugador_enemigo.username}", 
                    "victoria": True, 
                    "posiciones": res_pos
                }
            
            # Si no es victoria pero se hunde un barco
            if isinstance(es_impacto, dict):
                return {
                    "estado": "hundido", 
                    "mensaje": "¡HUNDIDO!", 
                    "victoria": False, 
                    "posiciones": es_impacto.get('posiciones')
                }

            return {
                "estado": "tocado", 
                "mensaje": "¡IMPACTO!", 
                "victoria": False
            }

        # Si no es impacto se devuelve agua
        return {"estado": False, "mensaje": "¡AGUA!", "victoria": False}

    def comprobar_casilla(self, columna, fila, disposicion):
        '''
        Comprueba la casilla donse se ha disparado para saber si impacta o no
        Modifica el tablero para guardar los cambios en la bd
        '''

        
        tablero_enemigo = disposicion.tablero
        valor_casilla = tablero_enemigo[fila][columna]

        if valor_casilla in ['X', 'B', 'T', 'H']:
            return "repetido"
        
        elif valor_casilla == 'A':
            tablero_enemigo[fila][columna] = 'X'
            es_impacto = False
        
        elif isinstance(valor_casilla, int):
            objeto_barco = Barco.objects.get(id = valor_casilla)
            self.tocar_barco(objeto_barco, tablero_enemigo, disposicion)
            
            if not objeto_barco.hundido:
                tablero_enemigo[fila][columna] = 'T'
                es_impacto = "tocado"
            else:
                es_impacto = {"estado": "hundido", "posiciones": objeto_barco.posiciones}

        # Modifica el tablero enemigo para guardar los cambios
        disposicion.tablero = tablero_enemigo
        disposicion.save()
        return es_impacto

    def tocar_barco(self, barco, tablero, disposicion):
        barco.vida -= 1
        
        if barco.vida <= 0:
            barco.hundido = True
            for fila, columna in barco.posiciones:
                tablero[fila][columna] = 'H'
            disposicion.tablero = tablero
            disposicion.save()
        barco.save()

    def comprobar_victoria(self, jugador_enemigo):
        # Devuelve True o False dependiendo si queda algun barco enemigo sib hundir
        barcos_enemigos = Barco.objects.filter( partida = self.partida_bd, jugador = jugador_enemigo)
        return not barcos_enemigos.filter(hundido = False).exists()


class Jugador:
    def __init__(self, nombre, tablero):
        self.nombre = nombre
        self.tablero = tablero


class CPU(Jugador):
    def __init__(self, tablero, memoria):
        super().__init__("CPU", tablero)
        self.memoria = memoria

    def decide_disparo(self, ronda):
        # Si hay disparos en cola 
        if self.memoria['cola_disparos']:
            proximo_disparo = self.memoria['cola_disparos'].pop(0)
            return [proximo_disparo['fila'], proximo_disparo['columna']]
        
        # Si hay en cola pero el ultimo disparo acierta genera nuevos posibles disparos
        ultimo_acierto = self.memoria.get('ultimo_disparo_acertado')
        if ultimo_acierto and ultimo_acierto['fila'] is not None:
            self.generar_posibles_disparos(ultimo_acierto['fila'], ultimo_acierto['columna'])
            
            # Si se generaron disparos válidos, usamos el primero de la nueva cola
            if self.memoria['cola_disparos']:
                proximo_disparo = self.memoria['cola_disparos'].pop(0)
                return [proximo_disparo['fila'], proximo_disparo['columna']]

        # 3. Si no hay rastro de barcos, disparo aleatorio (Modo Búsqueda)
        return self.obtener_disparo_aleatorio()

    def generar_posibles_disparos(self, fila, columna):
        # Guarda las coordenadas de alrededor
        direcciones = [
            {'fila': fila - 1, 'columna': columna},
            {'fila': fila + 1, 'columna': columna},
            {'fila': fila, 'columna': columna - 1},
            {'fila': fila, 'columna': columna + 1}
        ]
        
        # Aqui van las posiciones donde sabemos que no hya barcos
        ya_disparado = self.memoria['posiciones_descartadas'] + self.memoria['posicion_barcos_tocados']
        
        for dir in direcciones:
            f, c = dir['fila'], dir['columna']
            
            en_rango = (1 <= f <= 8) and (1 <= c <= 8)
            repetido = False
            for d in ya_disparado:
                if d['fila'] == f and d['columna'] == c:
                    repetido = True
            
            if en_rango and not repetido:
                self.memoria['cola_disparos'].append({'fila': f, 'columna': c})

    def obtener_disparo_aleatorio(self):
        # uno las dos listas de sitios ya usados
        lista1 = self.memoria['posiciones_descartadas']
        lista2 = self.memoria['posicion_barcos_tocados']
        ya_disparado = lista1 + lista2

        # sigue buscando hasta encontrar una casilla libre
        encontrado = False
        while encontrado == False:
            f = random.randint(1, 8)
            c = random.randint(1, 8)

            # comprobar que la casilla no este usada
            repetido = False
            for d in ya_disparado:
                if d['fila'] == f and d['columna'] == c:
                    repetido = True
                    break

            # si no esta repetida la devuelve
            if repetido == False:
                encontrado = True
                return [f, c]    


# ---------------- VISTAS QUE COMUNICAN CON EL FRONT----------------------

@login_required
def iniciar_partida(request):
    try:
        if request.method == 'POST':
            modo = request.POST.get('tipo')
            if modo == "1":
                cpu_user = User.objects.get(username='CPU')
                partida_bd = Partida.objects.create(jugador1=request.user, jugador2=cpu_user)
                partida_jugador = Jugador(request.user.username, None)
                request.session['cpu_memoria'] = {
                    'posiciones_descartadas': [],
                    'posicion_barcos_tocados': [],
                    'barcos_restantes': 11,
                    'cola_disparos': [],
                    'ultimo_disparo_acertado': {"fila": None, "columna": None}
                }
                memoria = request.session.get('cpu_memoria')
                partida_cpu = CPU(None, memoria)
                partida = Sesion_partida(partida_jugador, partida_cpu, partida_bd)
            
            else:
                data = json.loads(request.body)
                id_retador = data.get('id_retador')
                jugador_retador_user = User.objects.get(id=id_retador)
                
                # Crear partida primero
                partida_bd = Partida.objects.create(jugador1=request.user, jugador2=jugador_retador_user)
                
                # Crear objetos Jugador correctamente
                partida_jugador = Jugador(request.user.username, None)
                jugador_retador = Jugador(jugador_retador_user.username, None)
                
                partida = Sesion_partida(partida_jugador, jugador_retador, partida_bd)
                
            ronda_bd = Ronda.objects.create(partida = partida_bd, numero = 1)

            partida.crear_partida()
            request.session['partida_id'] = partida_bd.id
            request.session['partida_iniciada'] = True

            # Ambos jugadores dejan de buscar
            if modo != "1":
                Perfil.objects.filter(usuario__in=[request.user, jugador_retador_user]).update(buscando_partida=False)
        
            return redirect('partida:mostrar', partida_bd.id)
    except Exception as e:
        traceback.print_exc()
        return HttpResponse(f"Error al iniciar partida: {str(e)}")


@login_required
def mostrar_partida(request, partida_id):
    try:
        partida_bd = Partida.objects.get(id=partida_id)
        if not partida_bd.activa:
            return HttpResponse('Esta partida no es accesible')
        
        creador = (request.user == partida_bd.jugador1)
        retado = (request.user == partida_bd.jugador2)

        if not creador and not retado:
            return HttpResponse("No tienes permiso")
        
        # Set session for the user if they are a player
        request.session['partida_id'] = partida_id
        request.session['partida_iniciada'] = True
        
        j1_disposicion = DisposicionBarcos.objects.get(partida = partida_bd, jugador = partida_bd.jugador1)
        j2_disposicion = DisposicionBarcos.objects.get(partida = partida_bd, jugador =partida_bd.jugador2)

        if creador:
            enemigo_user = partida_bd.jugador2
            datos = {
                'jugador1': {'tablero': j1_disposicion.tablero, 'nombre': partida_bd.jugador1.username},
                'jugador2': {'nombre': partida_bd.jugador2.username}
            }
        else:
            enemigo_user = partida_bd.jugador1
            datos = {
                'jugador1': {'tablero': j2_disposicion.tablero, 'nombre': partida_bd.jugador2.username},
                'jugador2': {'nombre': partida_bd.jugador1.username}
            }
        
        # Añadir barcos enemigos restantes
        datos['barcos_enemigos'] = get_barcos_restantes(partida_bd, enemigo_user)
        return render(request, 'partida/partida.html', datos)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")


@login_required
def recibe_disparo(request):
    try:
        if request.method == 'POST':
            #Recoge las coordenadas del post
            coordenadas = json.loads(request.body)
        
            # Reconstruir el objeto de partida con los datos de la partida segun el ID
            partida_id = request.session['partida_id']
            sesion_partida = reconst_objeto_partida(request, partida_id)
            
            if sesion_partida.turno == 1:
                jugador_esperado = sesion_partida.partida_bd.jugador1
            else:
                jugador_esperado = sesion_partida.partida_bd.jugador2

            if request.user != jugador_esperado and not isinstance(sesion_partida.jugador2, CPU):
                return JsonResponse({"estado": False, "mensaje": "No es tu turno"})
            #MODO JVJ
            resultado_disparo = sesion_partida.ejecutar_turno(coordenadas)
            
            #Si tras realizar el disparo es victorio se cierra la sesion de la partida y se devuelve el disparo
            if resultado_disparo.get("victoria"):
                request.session['partida_iniciada'] = False
                return JsonResponse(resultado_disparo)

            # Siel jugador 2 es la CPU
            if isinstance(sesion_partida.jugador2, CPU):
                
                #Recibe las coordenadas del disparo
                coords_cpu_lista = sesion_partida.jugador2.decide_disparo(sesion_partida.ronda)
                f, c = coords_cpu_lista[0], coords_cpu_lista[1]
                
                #FUERZA EL TURNO 2 PARA EL J2 y almacena el resultado del disparo
                sesion_partida.turno = 2 
                coordenadas_cpu = {'x': f, 'y': c}
                resultado_cpu = sesion_partida.ejecutar_turno(coordenadas_cpu)
                
                # Guardar la memoria de la CPU dependiendo del resultado
                memoria = sesion_partida.jugador2.memoria
                if resultado_cpu.get("estado") in (True, 'tocado', 'hundido'): # IMPACTO
                    memoria['posicion_barcos_tocados'].append({"fila": f, "columna": c})
                    memoria['ultimo_disparo_acertado'] = {"fila": f, "columna": c}
                    if resultado_cpu.get("estado") == 'hundido':
                        memoria['cola_disparos'] = []
                        memoria['ultimo_disparo_acertado'] = {"fila": None, "columna": None}
                
                elif resultado_cpu.get("estado") == False: # AGUA
                    memoria['posiciones_descartadas'].append({"fila": f, "columna": c})
                    # Si falló, vaciamos el último acierto para que deje de buscar alrededor
                    if not memoria['cola_disparos']:
                        memoria['ultimo_disparo_acertado'] = {"fila": None, "columna": None}

                request.session['cpu_memoria'] = memoria
                
                #Mensaje que devuelve la CPU al javascript
                return JsonResponse({
                    "jugador": resultado_disparo,
                    "cpu": resultado_cpu,
                    "coords_cpu": {"x": f, "y": c},
                    "mensaje": resultado_cpu.get("mensaje", "Turno de la CPU"),
                    "barcos_enemigos": get_barcos_restantes(sesion_partida.partida_bd, sesion_partida.partida_bd.jugador2)
                })
            
            # Caso JvJ: añadir barcos del rival
            if request.user == sesion_partida.partida_bd.jugador1:
                enemigo = sesion_partida.partida_bd.jugador2
            else:
                enemigo = sesion_partida.partida_bd.jugador1
            
            #enemigo = sesion_partida.partida_bd.jugador2 if request.user == sesion_partida.partida_bd.jugador1 else sesion_partida.partida_bd.jugador1
            resultado_disparo['barcos_enemigos'] = get_barcos_restantes(sesion_partida.partida_bd, enemigo)
            return JsonResponse(resultado_disparo)
    
    except Exception as e:
        traceback.print_exc()
        return HttpResponse(f"Error: {str(e)}")


def terminar_partida(partida_bd, ganador, perdedor, es_abandono =False):
    '''
        Actualiza los datos de la partida una vez acabada
    '''
    perfil_ganador = Perfil.objects.get(usuario = ganador)
    perfil_ganador.partidas_ganadas += 1
    perfil_ganador.save()
    
    perfil_perdedor = Perfil.objects.get(usuario = perdedor)
    perfil_perdedor.partidas_perdidas += 1
    if es_abandono:
        perfil_perdedor.partidas_abandonadas += 1
    perfil_perdedor.save()
    
    partida_bd.ganador = ganador
    partida_bd.activa = False
    partida_bd.save()


@login_required
def abandonar_partida(request):
    '''
    Vista que recoge que usuario ha presionado el boton de abandonar
    1. Busca quien es el jugador 
    2. Fuerza que termine la partida
    3. Actualiza los datos de la partida
    4. Redirige al home
    '''
    try:
        partida_id = request.session.get('partida_id')
        partida_bd = Partida.objects.get(id = partida_id)
        ganador, perdedor = asignar_ganador_perdedor(request.user, partida_bd)
        terminar_partida(partida_bd, ganador, perdedor, es_abandono =True)
        request.session['partida_iniciada'] = False
        return redirect('inicial:home')
    except Exception as e:
        return HttpResponse(f"Error: {e}")


def asignar_ganador_perdedor(perdedor, partida_bd):
    if partida_bd.jugador1_id == perdedor.id:
        ganador = partida_bd.jugador2
    else:
        ganador = partida_bd.jugador1
    return ganador, perdedor


def reconst_objeto_partida(request, partida_id):
    '''
    Esta funcion crea un nuevo objeto de la partida pero con los datos actualizados
    '''

    # Recoge los datos de la bd
    partida_bd = Partida.objects.get(id=partida_id)
    barcos_j1 = DisposicionBarcos.objects.get(partida = partida_bd, jugador  =partida_bd.jugador1)
    barcos_j2 = DisposicionBarcos.objects.get(partida = partida_bd, jugador = partida_bd.jugador2)
    jugador1 = Jugador(partida_bd.jugador1.username, barcos_j1.tablero)
    
    # Comprobar si el j2 es cpu o un usuario
    if partida_bd.jugador2.username == 'CPU':
        jugador2 = CPU(barcos_j2.tablero, request.session.get('cpu_memoria'))
    else:
        jugador2 = Jugador(partida_bd.jugador2.username, barcos_j2.tablero)
    
    sesion = Sesion_partida(jugador1, jugador2, partida_bd)
    
    # Actualizar el turno y ronda
    ultimo_turno = Turno.objects.filter(ronda__partida=partida_bd).order_by('-id').first()
    if ultimo_turno:
        if ultimo_turno.jugador_dispara == partida_bd.jugador1:
            sesion.turno = 2
        else:
            sesion.turno = 1

    ultima_ronda = Ronda.objects.filter(partida = partida_bd).order_by('-numero').first()
    if ultima_ronda:
        sesion.ronda = ultima_ronda.numero
        
    return sesion



@login_required
def turno_jugador(request):
    """
    Se encarga de comunicar al usuario lo que va pasando en la partida.
    """
    try:
        partida_id = request.session.get('partida_id')
        partida_bd = Partida.objects.get(id=partida_id)

        if not partida_bd.activa:
            return JsonResponse({'es_turno_jugador': False, 'partida_terminada': True, 'mensaje': 'La partida ha terminado'})

        # Último turno registrado en BD
        ultimo_turno = Turno.objects.filter(ronda__partida=partida_bd).order_by('-id').first()

        if ultimo_turno is None:
            es_turno_jugador = (request.user == partida_bd.jugador1)
            mensaje = '¡Es tu turno!' if es_turno_jugador else 'Esperando al rival...'
            emisor = 'Sistema'
        else:
            es_turno_jugador = (ultimo_turno.jugador_dispara != request.user)
            if es_turno_jugador:
                # El rival ya disparó y ahora es mi turno. Buscamos el resultado de ese disparo.
                try:
                    disparo = Disparo.objects.get(turno=ultimo_turno)
                    res = disparo.resultado
                    if res == "False" or res == "agua": res_msg = "¡AGUA!"
                    elif res == "tocado": res_msg = "¡IMPACTO!"
                    elif res == "hundido": res_msg = "¡HUNDIDO!"
                    else: res_msg = f"Disparo: {res}"
                    
                    mensaje = f"{res_msg} - ¡Es tu turno!"
                    emisor = ultimo_turno.jugador_dispara.username
                except:
                    mensaje = '¡Es tu turno!'
                    emisor = 'Sistema'
            else:
                mensaje = 'Esperando al rival...'
                emisor = 'Sistema'

        # Coge el tablero del jugador para mostrar en su pantalla lo que está pasando
        mi_disposicion = DisposicionBarcos.objects.get(partida = partida_bd, jugador = request.user)

        # Barcos enemigos que quedan por hundir
        if request.user == partida_bd.jugador1:
            enemigo = partida_bd.jugador2  
        else: 
            enemigo = partida_bd.jugador1
        barcos_enemigos = get_barcos_restantes(partida_bd, enemigo)

        return JsonResponse({
            'es_turno_jugador': es_turno_jugador,
            'partida_terminada': False,
            'tablero_actualizado': mi_disposicion.tablero,
            'mensaje': mensaje,
            'emisor': emisor,
            'barcos_enemigos': barcos_enemigos
        })

    except Exception as e:
        return JsonResponse({'es_turno_jugador': False, 'partida_terminada': False })


def get_barcos_restantes(partida_bd, jugador_enemigo):
    # Esta funcion devuelve los barcos que quedan por hundir
    barcos = Barco.objects.filter( partida =partida_bd, jugador = jugador_enemigo, hundido = False)
    barcos_restantes = {}
    
    for b in barcos:
        barcos_restantes[b.nombre] = barcos_restantes.get(b.nombre, 0) + 1
    return barcos_restantes