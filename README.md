# 🚢 Hundir la Flota — Battleship Web

Juego de **Hundir la Flota** multijugador accesible desde el navegador, desarrollado con **Django + JavaScript**. Permite jugar contra la CPU o retar a otros jugadores conectados en tiempo real.

---

Si tienes un usuario accede mediante la siguiente IP al proyectyo desplegado en un servidor aws con nginx y gunicorn.

[Hundir la flota](13.222.117.222)

---

## 📋 Índice

- [Descripción](#descripción)
- [Tecnologías](#tecnologías)
- [Instalación](#instalación)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Pantallas](#pantallas)
- [Esquema de Llamadas y Base de Datos](#esquema-de-llamadas-y-base-de-datos)
- [Diagrama UML — Modelos](#diagrama-uml--modelos)
- [Diagrama UML — Clases](#diagrama-uml--clases)

---

## Descripción

El sistema permite a usuarios registrados iniciar sesión y competir en partidas de Hundir la Flota. **No es posible registrarse** desde la web — los usuarios son creados exclusivamente por el administrador.

Funcionalidades principales:

- Jugar contra la **CPU** con lógica de búsqueda y ataque inteligente
- Jugar contra **otro jugador** conectado mediante sistema de retos en el Lobby
- **Ranking** global con estadísticas de victorias, derrotas y abandonos
- **Panel de administración** exclusivo para superusuarios: crear, editar, eliminar usuarios y exportar datos en `.json`
- Gestión automática de turnos, impactos y barcos hundidos en tiempo real

---

## Tecnologías

| Tecnología | Uso |
|---|---|
| **Python 3.12 / Django** | Backend, lógica de negocio, ORM, autenticación |
| **JavaScript (AJAX)** | Interactividad en tiempo real, polling de turnos, actualización de tableros |
| **HTML / CSS** | Estructura y diseño visual con variables CSS |
| **SQLite / Django ORM** | Base de datos relacional |
| `json` | Comunicación de datos entre frontend y backend |
| `random` | Posicionamiento aleatorio de barcos y lógica de la CPU |
| **Django Auth** | Gestión de sesiones y seguridad |

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/HugoLopez21/BattleShip_Web_Game_Django.git
BattleShip_Web_Game_Django

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear vuestra base de datos y configurar settings.py

# 5. Aplicar migraciones
python manage.py migrate

# 6. Crear superusuario (administrador)
python manage.py createsuperuser

# 7. Crear usuario especial CPU (requerido para modo vs CPU)
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user('CPU', password='cpu')"

# 8. Lanzar servidor
python manage.py runserver
```

---

## Estructura del Proyecto

```
PRACTICA_T2/
│
├── manage.py
├── requirements.txt
│
├── practica_t2/                  # Configuración global Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── static/                       # Estáticos globales
│   ├── css/
│   │   └── general.css
│   ├── js/
│   └── img/
│
├── inicial/                      # App: login, home, lobby
│   ├── models.py                 # Modelo: Reto
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── templates/
│   │   ├── inicial/
│   │   │   ├── home.html
│   │   │   └── lobby.html
│   │   └── registration/
│   │       └── login.html
│   └── static/inicial/
│       ├── css/  (home.css, login.css, lobby.css)
│       └── js/   (lobby.js)
│
├── partida/                      # App: lógica del juego
│   ├── models.py                 # Modelos: Partida, Barco, Ronda, Turno, Disparo, DisposicionBarcos
│   ├── views.py                  # Clases: Sesion_partida, Jugador, CPU + vistas
│   ├── urls.py
│   ├── templates/partida/
│   │   └── partida.html
│   └── static/partida/
│       ├── css/   (partida.css)
│       ├── js/    (partida.js)
│       └── media/ (agua.png, barco.jpg, question.png)
│
└── admin_panel/                  # App: panel de administración
    ├── models.py                 # Modelo: Perfil
    ├── views.py
    ├── urls.py
    ├── forms.py
    ├── templates/admin_panel/
    │   ├── panel_administrador.html
    │   └── editar.html
    └── static/admin_panel/
        └── css/ (admin.css)
```

---

## Pantallas

### Login
Pantalla de acceso. Identifica al usuario y redirige a **Home** o, si es administrador, al **Panel de Administración**.

### Panel de Administración
Exclusivo para superusuarios. Permite:
- Crear, editar y eliminar usuarios
- Descargar datos de ranking, partidas y usuarios en formato `.json`

### Home
Muestra el **ranking** global de jugadores ordenado por victorias. Dos botones de acceso:
- **Jugar contra CPU** → entra directamente en partida
- **Buscar otro jugador** → accede al Lobby

### Lobby
Muestra los usuarios activos en ese momento. Permite enviar un reto (el retado recibe una alerta de confirmación). Al aceptar, ambos son redirigidos al tablero de juego.

### Pantalla de Juego
Dos tableros (propio y enemigo), consola de mensajes con el resultado de cada disparo y botón **Abandonar** que redirige a Home.

---

## Esquema de Llamadas y Base de Datos

### A · Login

```
Frontend                    Servidor                        BD
   │                            │                            │
   │─── POST inicial:login ────►│                            │
   │    (username / password)   │──── SELECT auth_user ─────►│
   │                            │◄─── usuario verificado ────│
   │                            │──── INSERT django_session ►│
   │◄── 302 redirect → home ────│                            │
```

| Paso | Tipo | Función | Operación BD |
|---|---|---|---|
| Envío credenciales | POST | `LoginView.post()` | `SELECT` en `auth_user` |
| Crear sesión | SESSION | `login()` | `INSERT` en `django_session` |
| Redirección | 302 | `redirect('inicial:home')` | — |

---

### B · Juego vs CPU

```
Frontend                    Servidor                        BD
   │                            │                            │
   │─── POST partida:iniciar ──►│──── SELECT auth_user ─────►│ (busca CPU)
   │                            │──── INSERT Partida ────────►│
   │                            │──── INSERT Barco (×11) ────►│
   │                            │──── INSERT DisposicionBarcos►│
   │◄── redirect tablero ───────│                            │
   │                            │                            │
   │─── AJAX POST disparo ─────►│──── SELECT DisposicionBarcos►│
   │    (coordenadas)           │──── INSERT Turno + Disparo ►│
   │                            │──── UPDATE Barco (vida--) ─►│
   │                            │  [CPU.decide_disparo()]     │
   │◄── JsonResponse ───────────│                            │
   │   {resultado_j1, cpu, coords_cpu}                       │
```

| Paso | Tipo | Función | Operación BD |
|---|---|---|---|
| Iniciar partida | POST | `iniciar_partida()` | `SELECT` CPU · `INSERT` Partida + Barco + DisposicionBarcos |
| Disparo jugador | AJAX POST | `recibe_disparo()` | `SELECT` DisposicionBarcos · `INSERT` Turno + Disparo · `UPDATE` Barco |
| Lógica CPU | Interna | `CPU.decide_disparo()` | Memoria en sesión Django |

---

### C · Juego PvP

```
Frontend                    Servidor                        BD
   │                            │                            │
   │─── AJAX GET lobby_check ──►│──── UPDATE Perfil ────────►│ (ultima_actividad)
   │    (cada 2 segundos)       │──── SELECT Reto ───────────►│ (estado=False)
   │◄── JSON {retos pendientes}─│                            │
   │                            │                            │
   │─── AJAX POST inicial:retar►│──── INSERT Reto ───────────►│
   │                            │                            │
   │    [retado acepta]         │──── UPDATE Reto.estado ────►│
   │                            │──── INSERT Partida ────────►│
   │                            │──── INSERT Barco + Disposicion►│
   │◄── 302 → tablero ──────────│                            │
   │                            │                            │
   │─── AJAX GET turno_jugador ►│──── SELECT Turno ──────────►│ (último disparo)
   │    (polling, espera turno) │──── SELECT Disparo ────────►│ (resultado rival)
   │◄── JSON {es_turno, tablero}│                            │
```

| Paso | Tipo | Función | Operación BD |
|---|---|---|---|
| Polling lobby | AJAX GET | `lobby_check()` cada 2s | `UPDATE` Perfil · `SELECT` Reto |
| Enviar reto | AJAX POST | `inicial:retar` | `INSERT` Reto |
| Aceptar reto | — | — | `UPDATE` Reto · `INSERT` Partida + Barco + DisposicionBarcos |
| Polling turno | AJAX GET | `turno_jugador()` | `SELECT` Turno · `SELECT` Disparo |

---

## Diagrama UML — Modelos

```
       ┌──────────────────────────┐
       │  «django.contrib.auth»   │
       │          User            │
       │──────────────────────────│
       │ id           PK          │
       │ username  CharField      │
       │ password  CharField      │
       │ email     EmailField     │
       └───────────┬──────────────┘
                   │ O2O
                   ▼
       ┌──────────────────────────┐        ┌────────────────────────┐
       │     «admin_panel»        │        │      «inicial»         │
       │          Perfil          │◄─ FK ──│         Reto           │
       │──────────────────────────│        │────────────────────────│
       │ usuario  → User    O2O   │        │ retador → Perfil  FK   │
       │ nombre   CharField       │        │ retado  → Perfil  FK   │
       │ apellido CharField       │        │ estado  BooleanField   │
       │ foto_perfil ImageField   │        └────────────────────────┘
       │ partidas_ganadas  Int    │
       │ partidas_perdidas Int    │
       │ partidas_abandonadas Int │
       │ buscando_partida  Bool   │
       │ ultima_actividad  DT     │
       └──────────────────────────┘

  User ──── FK ────►┌──────────────────────────┐
  (j1, j2, ganador) │       «partida»          │
                    │        Partida           │
                    │──────────────────────────│
                    │ jugador1  → User   FK    │
                    │ jugador2  → User   FK    │
                    │ ganador   → User   FK    │
                    │ fecha     DateTimeField  │
                    │ activa    BooleanField   │
                    └────┬──────┬──────┬───────┘
                         │      │      │
              FK ────────┘   FK │   FK └──────────
              ▼                 ▼                 ▼
 ┌─────────────────────┐  ┌──────────┐  ┌──────────────────────┐
 │  DisposicionBarcos  │  │  Ronda   │  │        Barco         │
 │─────────────────────│  │──────────│  │──────────────────────│
 │ partida → Partida FK│  │ partida  │  │ partida → Partida FK │
 │ jugador → User    FK│  │ numero   │  │ jugador → User    FK │
 │ tablero  JSONField  │  └────┬─────┘  │ nombre  CharField    │
 └─────────────────────┘       │ FK     │ tamaño  IntegerField │
                                ▼        │ vida    IntegerField │
                          ┌──────────┐   │ hundido BooleanField │
                          │  Turno   │   │ posiciones JSONField │
                          │──────────│   └──────────────────────┘
                          │ ronda FK │
                          │ jugador  │
                          └────┬─────┘
                               │ O2O
                               ▼
                         ┌───────────┐
                         │  Disparo  │
                         │───────────│
                         │ turno O2O │
                         │ coordenada│
                         │ resultado │
                         └───────────┘
```

---

## Diagrama UML — Clases

> Ubicación: `partida/views.py`

```
┌──────────────────────────────────────────────────────┐
│                    Sesion_partida                     │
│──────────────────────────────────────────────────────│
│ + partida_bd  : Partida                              │
│ + jugador1    : Jugador                              │
│ + jugador2    : Jugador | CPU                        │
│ + turno       : int  (1 | 2)                         │
│ + ronda       : int                                  │
│ + estado      : bool                                 │
│ + ganador     : User | None                          │
│──────────────────────────────────────────────────────│
│ + crear_partida()                                    │
│ - crear_tablero()              → list                │
│ - generar_barcos(jugador)      → list[Barco]         │
│ - comprobar_espacio(...)       → bool                │
│ - colocar_barco(barco, tablero)→ bool                │
│ - asignar_todos_barcos(tablero, lista)               │
│ + ejecutar_turno(coordenadas)  → dict                │
│ - cambiar_turno()                                    │
│ - siguiente_ronda()                                  │
│ + disparar(coords, enemigo, turno_bd) → dict         │
│ - comprobar_casilla(col, fila, disp)  → mixed        │
│ - tocar_barco(barco, tablero, disp)                  │
│ - comprobar_victoria(enemigo)  → bool                │
└──────────────────────────────────────────────────────┘
        ▲ usa                          ▲ usa
        │                             │
┌────────────────┐         ┌──────────────────────────┐
│    Jugador     │◄extends─│           CPU            │
│────────────────│         │──────────────────────────│
│ + nombre : str │         │ + memoria : dict         │
│ + tablero: list│         │──────────────────────────│
│────────────────│         │ + decide_disparo(ronda)  │
│ + __init__()   │         │ - generar_posibles_disp()│
└────────────────┘         │ - obtener_disparo_aleatorio()│
                           └──────────────────────────┘

┌──────────────────────────────┐     ┌────────────────────────────────┐
│  «module» Vistas Django      │     │  «helpers» Funciones aux.      │
│──────────────────────────────│     │────────────────────────────────│
│ @login_required              │     │ + reconst_objeto_partida()     │
│ + iniciar_partida(request)   │────►│ + terminar_partida(...)        │
│ + mostrar_partida(request)   │     │ + asignar_ganador_perdedor(...) │
│ + recibe_disparo(request)    │     │ + get_barcos_restantes(...)     │
│ + abandonar_partida(request) │     └────────────────────────────────┘
│ + turno_jugador(request)     │
└──────────────────────────────┘
```

**Relaciones:**
- `CPU` **hereda** de `Jugador` y extiende su comportamiento con lógica de disparo
- `Sesion_partida` **usa** instancias de `Jugador` o `CPU` según el modo de juego
- Las **Vistas** crean e instancian `Sesion_partida` en cada petición
- `reconst_objeto_partida()` reconstruye el objeto `Sesion_partida` en cada petición AJAX a partir del estado guardado en BD y sesión

---

## Flujo de navegación

```
                     ┌─────────┐
                     │  Login  │
                     └────┬────┘
               ┌──────────┴──────────┐
               │ admin               │ usuario normal
               ▼                     ▼
     ┌──────────────────┐       ┌──────────┐
     │ Panel Admin      │       │   Home   │
     │ (crear/editar/   │       │ (ranking)│
     │  eliminar users) │       └────┬─────┘
     └──────────────────┘            │
                          ┌──────────┴──────────┐
                          │ vs CPU               │ vs Jugador
                          ▼                      ▼
                     ┌─────────┐           ┌──────────┐
                     │ Partida │           │  Lobby   │
                     │ directa │           │ (retos)  │
                     └────┬────┘           └────┬─────┘
                          │                     │ acepta reto
                          │              ┌──────┘
                          ▼              ▼
                     ┌────────────────────┐
                     │  Tablero de Juego  │
                     │  (turnos via AJAX) │
                     └──────────┬─────────┘
                                │ victoria / abandono
                                ▼
                           ┌──────────┐
                           │   Home   │
                           └──────────┘
```

---

## Licencia

Proyecto académico — uso educativo.
