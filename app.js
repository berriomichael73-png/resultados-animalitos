const API_URL = "https://resultados-animalitos.onrender.com";

document.addEventListener("DOMContentLoaded", () => {
    obtenerResultados();
    setInterval(obtenerResultados, 60000);
});

async function obtenerResultados() {
    const contenedor = document.getElementById("contenedor-resultados");
    try {
        const response = await fetch(`${API_URL}/resultados`);
        if (!response.ok) throw new Error("Error en la respuesta del servidor");
        const data = await response.json();
        
        console.log("Datos recibidos:", data);
        window.todosLosDatos = data;
        renderizarTarjetas(data);
    } catch (error) {
        console.error("Error:", error);
        if (contenedor) {
            contenedor.innerHTML = `<p style="text-align: center; color: #ff5555; grid-column: 1 / -1;">Error al conectar con Render. Reintentando...</p>`;
        }
    }
}

function renderizarTarjetas(resultados) {
    const contenedor = document.getElementById("contenedor-resultados");
    if (!contenedor) return;
    
    contenedor.innerHTML = "";

    if (!Array.isArray(resultados) || resultados.length === 0) {
        contenedor.innerHTML = `<p style="text-align: center; color: #aaa; grid-column: 1 / -1;">No hay resultados disponibles en este momento.</p>`;
        return;
    }

    resultados.forEach(item => {
        const card = document.createElement("div");
        card.className = `card-sorteo ${item.realizado ? 'sorteo-realizado' : 'sorteo-pendiente'}`;

        card.innerHTML = `
            <div class="card-header">
                <img src="${item.logo_loteria}" alt="${item.loteria}" width="24" height="24" onerror="this.style.display='none'">
                <span>${item.loteria}</span>
            </div>
            <div class="card-body">
                <span class="hora-badge">⏰ ${item.hora}</span>
                <img src="${item.imagen_animal}" alt="${item.animal}" onerror="this.src='https://loteriadehoy.com/images/por-salir.png'">
                <h3>${item.numero !== '--' ? item.numero + ' - ' : ''}${item.animal}</h3>
            </div>
        `;

        contenedor.appendChild(card);
    });
}
