
async function retar(retado_id){
    //Envia el id del usuario retado
    const response = await fetch('/retar/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({retado_id})
    })
    const data = await response.json();
    console.log(data.mensaje)
}


let buscando = true;
setInterval( async () => {
    // Cada 5 segundos llama al servidor para ver si alguien le ha retado
    if (!buscando){
        return;
    }
    const response = await fetch('/lobby_check/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({})
    })
    const data = await response.json();
    
    //En caso de que si sale un mensaje
    if (data.retado){
        buscando = false; 
        const acepto = confirm(data.mensaje);
        //Acepta el reto envia el id del retador y el J1 siempres es el jugador retado
        if (acepto) {
            alert("¡Has aceptado! Redirigiendo...");
            aceptarReto(data.id_retador);
        } else {
            // Si rechaza vuelve a buscar
            setTimeout(() => { 
                buscando = true; 
            }, 5000);
        }
    } else if (data.partida_iniciada) {
        // redirigir a la partida identificandola con la id
        buscando = false;
        window.location.href = `/juego/tablero/${data.partida_id}/`;
    }
}, 5000);



async function aceptarReto(id_retador){
    const response = await fetch(`${rutaIniciarPartida}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({id_retador})
    })

    // Redirigir a la url que manda el servidor
    if (response.redirected) {
        window.location.href = response.url;
        return;
    }
}

