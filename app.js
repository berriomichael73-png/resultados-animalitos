const API_URL = "https://resultados-animalitos.onrender.com"; // Reemplaza con tu URL exacta de Render

document.addEventListener("DOMContentLoaded", () => {
    obtenerResultados();
    // Actualiza los resultados automáticamente en el frontend cada 60 segundos
    setInterval(obtenerResultados, 60000);
});

async function obtenerResultados() {
    try {
        const response = await fetch(`${API_URL}/resultados`);
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        const data = await response.json();
        renderizarTarjetas(data);
        generarFiltrosLoterias(data);
    } catch (error) {
        console.error("Error al obtener los resultados:", error);
    }
}

function renderizarTarjetas(resultados) {
    const contenedor = document.getElementById("contenedor-resultados");
    if (!contenedor) return;
    
    contenedor.innerHTML = "";

    resultados.forEach(item => {
        // Corrección de la variable card para evitar 'card is not defined'
        const card = document.createElement("div");
        card.className = "card-sorteo";
        if (item.realizado) {
            card.classList.add("sorteo-realizado");
        } else {
            card.classList.add("sorteo-pendiente");
        }

        card.innerHTML = `
            <div class="card-header" style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <img src="${item.logo_loteria}" alt="${item.loteria}" style="width: 28px; height: 28px; object-fit: contain;" onError="this.style.display='none'">
                <span style="font-weight: bold; font-size: 0.9rem;">${item.loteria}</span>
            </div>
            <div class="card-body" style="text-align: center;">
                <span class="hora-badge" style="background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">⏰ ${item.hora}</span>
                <img src="${item.imagen_animal}" alt="${item.animal}" style="width: 70px; height: 70px; object-fit: contain; margin: 10px auto; display: block;" onError="this.src='https://loteriadehoy.com/images/por-salir.png'">
                <h3 style="margin: 4px 0; font-size: 1.1rem;">${item.numero !== '--' ? item.numero + ' - ' : ''}${item.animal}</h3>
            </div>
        `;

        contenedor.appendChild(card);
    });
}

function generarFiltrosLoterias(resultados) {
    const contenedorFiltros = document.getElementById("contenedor-filtros");
    if (!contenedorFiltros || contenedorFiltros.children.length > 1) return;

    const loteriasUnicas = [...new Set(resultados.map(item => item.loteria))];

    loteriasUnicas.forEach(loteria => {
        const btn = document.createElement("button");
        btn.className = "btn-filtro";
        btn.innerText = loteria;
        btn.onclick = () => filtrarPorLoteria(loteria, resultados, btn);
        contenedorFiltros.appendChild(btn);
    });
}

function filtrarPorLoteria(nombreLoteria, todosLosResultados, elementoBoton) {
    document.querySelectorAll(".btn-filtro").forEach(b => b.classList.remove("active"));
    elementoBoton.classList.add("active");

    if (nombreLoteria === "Todas") {
        renderizarTarjetas(todosLosResultados);
    } else {
        const filtrados = todosLosResultados.filter(item => item.loteria === nombreLoteria);
        renderizarTarjetas(filtrados);
    }
}
