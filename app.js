const API_URL = "https://resultados-animalitos.onrender.com"; 

document.addEventListener("DOMContentLoaded", () => {
    obtenerResultados();
    setInterval(obtenerResultados, 60000);
});

function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    sidebar.classList.toggle("open");
    overlay.classList.toggle("open");
}

async function obtenerResultados() {
    const contenedor = document.getElementById("contenedor-resultados");
    try {
        const response = await fetch(`${API_URL}/resultados`);
        if (!response.ok) throw new Error("Error en la red");
        const data = await response.json();
        
        window.todosLosDatos = data; 
        renderizarTarjetas(data);
        generarFiltrosLoterias(data);
    } catch (error) {
        console.error("Error al obtener los resultados:", error);
        if (contenedor) {
            contenedor.innerHTML = `
                <div class="loading-state">
                    <i class="fa-solid fa-triangle-exclamation" style="color: #ef4444;"></i>
                    <p>Error al conectar con Render. Reintentando...</p>
                </div>
            `;
        }
    }
}

function renderizarTarjetas(resultados) {
    const contenedor = document.getElementById("contenedor-resultados");
    if (!contenedor) return;
    
    contenedor.innerHTML = "";

    if (!Array.isArray(resultados) || resultados.length === 0) {
        contenedor.innerHTML = `
            <div class="loading-state">
                <p>No hay resultados disponibles en este momento.</p>
            </div>
        `;
        return;
    }

    resultados.forEach(item => {
        const card = document.createElement("div");
        card.className = `card-sorteo ${item.realizado ? 'sorteo-realizado' : 'sorteo-pendiente'}`;

        card.innerHTML = `
            <div class="card-top">
                <div class="loteria-info">
                    <img src="${item.logo_loteria}" alt="${item.loteria}" onerror="this.style.display='none'">
                    <span>${item.loteria}</span>
                </div>
                <span class="hora-badge">${item.hora}</span>
            </div>
            <div class="card-content">
                <img src="${item.imagen_animal}" alt="${item.animal}" onerror="this.src='https://loteriadehoy.com/images/por-salir.png'">
                <h3>${item.numero !== '--' ? item.numero + ' - ' : ''}${item.animal}</h3>
            </div>
        `;

        contenedor.appendChild(card);
    });
}

function generarFiltrosLoterias(resultados) {
    const contenedorFiltros = document.getElementById("contenedor-filtros");
    if (!contenedorFiltros || contenedorFiltros.children.length > 0) return;

    // Botón "Todas"
    const btnTodas = document.createElement("button");
    btnTodas.className = "btn-filtro active";
    btnTodas.innerHTML = `<i class="fa-solid fa-fire"></i> Todas las Loterías`;
    btnTodas.onclick = () => {
        filtrarPorLoteria('Todas', resultados, btnTodas);
        toggleSidebar();
    };
    contenedorFiltros.appendChild(btnTodas);

    const loteriasUnicas = [...new Set(resultados.map(item => item.loteria))];

    loteriasUnicas.forEach(loteria => {
        const btn = document.createElement("button");
        btn.className = "btn-filtro";
        btn.innerHTML = `<i class="fa-solid fa-ticket"></i> ${loteria}`;
        btn.onclick = () => {
            filtrarPorLoteria(loteria, resultados, btn);
            toggleSidebar();
        };
        contenedorFiltros.appendChild(btn);
    });
}

function filtrarPorLoteria(nombreLoteria, todosLosResultados, elementoBoton) {
    document.querySelectorAll(".btn-filtro").forEach(b => b.classList.remove("active"));
    elementoBoton.classList.add("active");

    const labelFiltro = document.getElementById("filtro-activo-label");

    if (nombreLoteria === "Todas") {
        labelFiltro.innerHTML = `<i class="fa-solid fa-fire"></i> Mostrando: Todas las Loterías`;
        renderizarTarjetas(todosLosResultados);
    } else {
        labelFiltro.innerHTML = `<i class="fa-solid fa-ticket"></i> Mostrando: ${nombreLoteria}`;
        const filtrados = todosLosResultados.filter(item => item.loteria === nombreLoteria);
        renderizarTarjetas(filtrados);
    }
}
