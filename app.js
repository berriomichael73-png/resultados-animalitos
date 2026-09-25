const API_URL = "https://resultados-animalitos.onrender.com"; 

document.addEventListener("DOMContentLoaded", () => {
    obtenerResultados();
    setInterval(obtenerResultados, 60000);
});

async function obtenerResultados() {
    try {
        const response = await fetch(`${API_URL}/resultados`);
        if (!response.ok) throw new Error("Error en la red");
        const data = await response.json();
        
        window.todosLosDatos = data; 
        renderizarTarjetas(data);
        generarFiltrosLoterias(data);
    } catch (error) {
        console.error("Error al obtener los resultados:", error);
        document.getElementById("contenedor-resultados").innerHTML = `
            <p style="text-align: center; color: #f85149; grid-column: 1 / -1; padding: 20px;">Error al conectar con el servidor. Reintentando...</p>
        `;
    }
}

function renderizarTarjetas(resultados) {
    const contenedor = document.getElementById("contenedor-resultados");
    if (!contenedor) return;
    
    contenedor.innerHTML = "";

    resultados.forEach(item => {
        const card = document.createElement("div");
        card.className = `card-sorteo ${item.realizado ? 'sorteo-realizado' : 'sorteo-pendiente'}`;

        card.innerHTML = `
            <div class="card-header-loteria">${item.loteria}</div>
            <div class="card-middle">
                <span class="hora-badge">⏰ ${item.hora}</span>
            </div>
            <div class="card-body">
                <img src="${item.imagen_animal}" alt="${item.animal}" onerror="this.src='https://loteriadehoy.com/images/por-salir.png'">
                <h3>${item.numero !== '--' ? item.numero + ' - ' : ''}${item.animal}</h3>
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
