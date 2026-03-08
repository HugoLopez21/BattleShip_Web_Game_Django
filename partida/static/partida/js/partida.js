//El jugador que comunica siempres es j1
window.onload = () => {

    // coger datos del tablero del j1
    const datosJugador1 = JSON.parse(document.getElementById('datos-j1').textContent);

    // divs donde van las casillas
    const tableroJ1 = document.querySelector('#j1 .tablero');
    const tableroJ2 = document.querySelector('#j2 .tablero');

    const mensajePartida = document.getElementById('mensaje_partida');
    const divBarcosEnemigos = document.querySelector('.barcos_enemigos');

    let turnoJ1 = false;
    let juegoFinalizado = false;

    const nombreJ1 = datosJugador1.nombre;
    const nombreJ2 = document.getElementById('nombre_j2').textContent;



    // ------------------ MONTAR TABLEROS ---------------------

    function montarTableroJ1() {
        // La función monta el tablero con casillas y sus coordenadas

        tableroJ1.innerHTML = '';
        const matriz = datosJugador1.tablero;

        // recorre la matriz sin contar los bordes
        for (let i = 1; i <= 8; i++) {
            for (let j = 1; j <= 8; j++) {

                // crear div de la casilla y asignarle las coordenadas de la matriz
                const casilla = document.createElement('div');
                casilla.classList.add('casilla');
                casilla.dataset.x = i;
                casilla.dataset.y = j;
                const valor = matriz[i][j];

                // pinto la casilla segun el valor y  la añade
                pintarCasilla(casilla, valor, true);
                tableroJ1.appendChild(casilla);
            }
        }
    }



    function montarTableroJ2() {
        // misma funcion que la anterior pero el contenido de todas las casillas son interrogantes
        // Ademas añade a cada casilla un evento clicable para poder ejecutar el disparo
        tableroJ2.innerHTML = '';

        for (let i = 1; i <= 8; i++) {
            for (let j = 1; j <= 8; j++) {

                const casilla = document.createElement('div');
                casilla.classList.add( 'casilla', 'pregunta');
                casilla.dataset.x = i;
                casilla.dataset.y = j;
                casilla.innerHTML = `<span>?</span>`;

                // Envia las coordenadas del disparo al servidor
                casilla.addEventListener('click', () => {
                    disparar(i, j, casilla);
                });
                tableroJ2.appendChild(casilla);
            }
        }
    }



    function pintarCasilla(div, valor, esJ1) {
        // si no viene esJ1 false por defecto
        if (esJ1 === undefined) {
            esJ1 = false;
        }
        // Resetea el contenido
        div.innerHTML = '';
        div.className = 'casilla';

        if (valor === 'A') {
            // agua vacia, no pinto nada

        } else if (valor === 'X') {
            // disparo fallido, pongo imagen de agua
            const img = document.createElement('img');
            img.src = rutasImagenes.agua;
            div.appendChild(img);
            div.classList.add('agua');

        } else if (valor === 'T') {
            // tocado -naranja
            div.classList.add('tocado');

        } else if (valor === 'H') {
            // hundido - rojo
            div.classList.add('hundido');

        } else if (typeof valor === 'number' && esJ1 === true) {
            // si es el barco del jugador 1 pone imagen de un barco en la casilla
            const img = document.createElement('img');
            img.src = rutasImagenes.barco;
            div.appendChild(img);
            div.classList.add('barco');
        }
    }

    function actualizarLeyendaBarcos(barcos) {
        // Limpiamos y repintamos la leyenda
        divBarcosEnemigos.innerHTML = '<h4>Barcos Enemigos Restantes</h4>';
        
        // El diccionario viene con Nombre: Cantidad
        for (const [nombre, cantidad] of Object.entries(barcos)) {
            const p = document.createElement('p');
            p.classList.add('item_barco');
            p.innerHTML = `<strong>${nombre}:</strong> ${cantidad}`;
            divBarcosEnemigos.appendChild(p);

        }
        if (Object.keys(barcos).length === 0) {
            divBarcosEnemigos.innerHTML += '<p>¡Todos hundidos!</p>';
        }
    }


    // ------------------ ENVIAR DISPARO AL SERVIDOR ---------------------

    async function disparar(x, y, divOriginal) {
        // si no es el turno del jugador y si el juego ya termino 
        if (!turnoJ1) return;
        if (juegoFinalizado) return;
        const noHacerNada = ['tocado', 'agua', 'hundido'];
        // si ya dispare en esa casilla no hago nada (usamos some porque classList no tiene includes(array))
        if (noHacerNada.some(clase => divOriginal.classList.contains(clase))) {
            return;
        }
        turnoJ1 = false;
        
        try {
            const response = await fetch('/juego/disparar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ x: x, y: y })
            });

            const data = await response.json();

            // si ya ha disparado ahi no devuelve nada
            if (data.mensaje === "No se puede volver a disparar aquí") {
                turnoJ1 = true;
                actualizarMensaje( "Sistema", data.mensaje, "agua");
                return;
            }

            // resultado del jugador a veces viene en data.jugador y a veces viene directo en data
            const resultadoJugador = data.jugador || data;

            // mostarr el mensaje del servidor
            if (resultadoJugador.estado === false) {
                actualizarMensaje( nombreJ1, resultadoJugador.mensaje, "agua");
            } else {
                actualizarMensaje(nombreJ1, resultadoJugador.mensaje, resultadoJugador.estado);
            }

            if (resultadoJugador.estado === 'tocado' || resultadoJugador.estado === 'hundido') {

                // En caso de hundir el barco recibe toda las posiciones para colorearlos todos
                if (resultadoJugador.estado === 'hundido' && resultadoJugador.posiciones) {
                    resultadoJugador.posiciones.forEach(p => {
                        const casillaEnemiga =tableroJ2.querySelector(`.casilla[data-x="${p[0]}"][data-y="${p[1]}"]`);
                        if (casillaEnemiga) {
                            pintarCasilla( casillaEnemiga, 'H', false );
                        }
                    });

                } else {
                    pintarCasilla(divOriginal, 'T', false);
                }

                // comprobar la victoria una vez tocado el barco
                if (resultadoJugador.victoria) {
                    finalizarPartida( "Sistema", resultadoJugador.mensaje);
                    return;
                }

            } else {
                // fallo
                pintarCasilla(divOriginal,'X', false);
            }

            // si se juega conta la cpu es su turno
            if (data.cpu) {
                setTimeout(() => {
                    turnoCPU(data.cpu, data.coords_cpu, data.mensaje);
                }, 800);
            } else {
                // si es contra otro jugador se espera
                esperarTurnoRival();
            }

            // actualizar leyenda de barcos si viene en la respuesta
            if (resultadoJugador.barcos_enemigos) {
                actualizarLeyendaBarcos(resultadoJugador.barcos_enemigos);
            } else if (data.barcos_enemigos) {
                actualizarLeyendaBarcos(data.barcos_enemigos);
            }

        } catch (error) {
            console.error(error);
            turnoJ1 = true
        }
    }


    // ---------------- TURNOS ---------------------
    function turnoCPU(resultadoCpu, coordenadas, mensaje) {
        actualizarMensaje("Cpu", mensaje, "agua");

        setTimeout(() => {
            // saca la casilla donde ha disparado la cpu
            const casillaJ1 = tableroJ1.querySelector(`.casilla[data-x="${coordenadas.x}"][data-y="${coordenadas.y}"]`);

            if (resultadoCpu.estado === 'tocado' || resultadoCpu.estado === 'hundido') {
                // si hya barco hundido pinta todas las casillas
                if (resultadoCpu.estado === 'hundido' && resultadoCpu.posiciones) {
                    resultadoCpu.posiciones.forEach(pos => {
                        const casilla = tableroJ1.querySelector(`.casilla[data-x="${pos[0]}"][data-y="${pos[1]}"]`);
                        if (casilla) {
                            pintarCasilla(casilla, 'H', true);
                        }
                    });
                } else if (casillaJ1) {
                    pintarCasilla(casillaJ1, 'T', true);
                }

            } else if (casillaJ1) {
                pintarCasilla(casillaJ1, 'X', true);
            }

            if (resultadoCpu.estado === false) {
                //Falla
                actualizarMensaje("Cpu", resultadoCpu.mensaje, "agua");
            } else {
                //Acierta
                actualizarMensaje("Cpu", resultadoCpu.mensaje, resultadoCpu.estado);
            }

            // comprueba si ha ganado
            if (resultadoCpu.victoria) {
                setTimeout( () => {
                    finalizarPartida( "Sistema", resultadoCpu.mensaje);
                },1000 );
            } else {
                // si no ha ganado vuelve a habilitar el turno
                setTimeout( () => {
                    actualizarMensaje( "Sistema", "¡Es tu turno!", "agua");
                    turnoJ1 = true;
                }, 1200 );
            }
        }, 1000);
    }

    // ---------------- ESPERAR TURNO------------------

    let tiempoRefresco = null;
    function esperarTurnoRival() {
        // Definimos una funcion que cada 2 segundos va hablando con el servidor para saber el estado de la partida
        

        // si ya habia un intervalo lo paro
        if (tiempoRefresco) {
            clearInterval(tiempoRefresco);
        }
        tiempoRefresco = setInterval(async () => {
            try {
                const response = await fetch('/juego/turno_jugador/');
                const data = await response.json();

                // si el servidor manda barcos enemigos se actualiza la leyenda
                if (data.barcos_enemigos) {
                    actualizarLeyendaBarcos(data.barcos_enemigos);
                }

                // si el servidor manda tablero se actualiza 
                if (data.tablero_actualizado) {
                    actualizarTableroJ1(data.tablero_actualizado);
                }

                // si el servidor manda un mensaje se muestra por pantalla
                if (data.mensaje) {
                    actualizarMensaje(data.emisor || "Sistema", data.mensaje, data.es_turno_jugador ? "agua" : "");
                }

                // comprueba si la partida ha terminado
                if (data.partida_terminada) {
                    clearInterval(tiempoRefresco);
                    finalizarPartida( "Sistema", data.mensaje);
                    return;
                }

                // dice si es el turno del jugador 1
                if (data.es_turno_jugador) {
                    clearInterval(tiempoRefresco);
                    turnoJ1 =true;
                }
            } catch (e) {
                console.error(e);
            }
        }, 2000);
    }



    function actualizarTableroJ1(matriz) {
        //Actualiza el tablero del jugador cuando recibe un disparo
        for ( let i = 1; i <= 8; i++) {
            for ( let j = 1; j <= 8; j++) {
                const casilla = tableroJ1.querySelector(`.casilla[data-x="${i}"][data-y="${j}"]`);
                const valor = matriz[i][j]
                // solo repinta si ya se ha disparado
                if (valor === 'X' || valor === 'T' || valor === 'H') {
                    // si ya estaba hundida no hace nada
                    if (!casilla.classList.contains('hundido')) {
                        pintarCasilla(casilla, valor, true);
                    }
                }
            }
        }
    }



    function actualizarMensaje(mensajeDe, texto, tipo) {
        //esta función recibe el texto a mostrar y el tipo de clase
        //Y lo muestra en pantalla

        if (tipo === undefined) {
            tipo = ""
        }

        mensajePartida.textContent = mensajeDe + ": " + texto;
        mensajePartida.className = 'fade-in ' + tipo;

        setTimeout(() => {
            mensajePartida.classList.remove( 'fade-in');
        }, 500);
    }



    function finalizarPartida(quien, texto) {
        juegoFinalizado = true;
        actualizarMensaje(quien, texto, "hundido");
        tableroJ2.style.pointerEvents ='none'; //No se puede clickar mas

        // parar el refresco
        if (tiempoRefresco) {
            clearInterval(tiempoRefresco);
        }
    }




    // -------------------- INICIAR TODO ----------------------------
    montarTableroJ1();
    montarTableroJ2();
    
    // Cargar leyenda inicial
    const barcosIniciales = JSON.parse(document.getElementById('barcos-enemigos').textContent);
    actualizarLeyendaBarcos(barcosIniciales);

    esperarTurnoRival();
};