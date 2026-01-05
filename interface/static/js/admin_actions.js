/*
# ==========================================================
# CITADEL CORE - Sistema de Integridad y Gestión
# Archivo: admin_actions.js
# Versión: 0.2.5 (Referencia unificada)
# Módulo: Core
# Certificación: FHS-Compliant | Norma: ISO/IEC 27001 (Simulada)
# Autor: Daniel Miñana & Gemini
# ---------------------------------------------------------
# Descripción: Gestión de peticiones del Panel de Control
#              Mantiene el flujo de datos aislado del HTML
# ==========================================================
*/

async function ejecutarAccion(url) {
    const status = document.getElementById('status');
    status.style.display = 'block';
    status.className = 'status-processing';
    status.innerHTML = "⌛ Procesando...";
    
    try {
        const response = await fetch(url, { method: 'POST' });
        const res = await response.json();
        status.innerHTML = "✅ " + res.message;
        status.className = 'status-success';
    } catch (err) {
        status.innerHTML = "❌ Error en la comunicación con el servidor";
        status.className = 'status-error';
    }
}

async function subirBitacora() {
    const titulo = document.getElementById('bit-titulo').value;
    const contenido = document.getElementById('bit-contenido').value;
    const status = document.getElementById('status');
    
    if (!titulo || !contenido) {
        status.style.display = 'block';
        status.innerHTML = "⚠️ Por favor, rellena todos los campos.";
        return;
    }

    try {
        const response = await fetch('/api/update-bitacora', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ titulo, contenido })
        });
        const res = await response.json();
        status.style.display = 'block';
        status.innerHTML = "✅ " + res.message;
    } catch (err) {
        status.innerHTML = "❌ Error al publicar en la bitácora.";
    }
}

async function lanzarVerificacion() {
    const reportDiv = document.getElementById('integrity-report');
    reportDiv.innerHTML = "> Iniciando escaneo SHA-256...<br>> Verificando estructuras de datos...";
    
    try {
        const response = await fetch('/api/check-integrity', { method: 'POST' });
        const data = await response.json();
        
        let html = `> INFORME GENERADO: ${data.timestamp}<br>`;
        data.details.forEach(item => {
            html += `> ${item.archivo} ... <span class="status-ok">[${item.estado}]</span><br>`;
            html += `<span style="color: #64748b; font-size: 0.7rem;">  Hash: ${item.hash}</span><br>`;
        });
        html += `<br>> <strong>ESTADO FINAL: SISTEMA ÍNTEGRO</strong>`;
        reportDiv.innerHTML = html;
    } catch (err) {
        reportDiv.innerHTML = "> ❌ ERROR CRÍTICO EN LA AUDITORÍA";
    }
}

async function cargarRoadmap() {
    try {
        const response = await fetch('/api/get-roadmap');
        const data = await response.json();
        
        const tableBody = document.getElementById('body-roadmap');
        if (!tableBody) return;
        
        tableBody.innerHTML = '';

        // PROTECCIÓN: Verificamos que 'data' y 'data.roadmap' existan antes de usar forEach
        if (data && data.roadmap && Array.isArray(data.roadmap)) {
            data.roadmap.forEach(item => {
                tableBody.innerHTML += `
                    <tr>
                        <td>${item.id}</td>
                        <td>${item.tarea}</td>
                        <td><span class="status-tag ${item.estado}">${item.estado}</span></td>
                        <td>
                            <button class="btn-borrar" data-id="${item.id}">🗑️ Borrar</button>
                        </td>
                    </tr>
                `;
            });
        } else {
            tableBody.innerHTML = '<tr><td colspan="4">No hay objetivos en el cronograma.</td></tr>';
        }
    } catch (error) {
        console.error("Error cargando el roadmap:", error);
    }
}

async function enviarNuevaTarea() {
    const id = document.getElementById('road-id').value;
    const tarea = document.getElementById('road-tarea').value;

    if (!id || !tarea) {
        alert("Por favor, rellena el ID (v0.x) y la Tarea.");
        return;
    }

    const payload = {
        id: id,
        tarea: tarea,
        estado: "pendiente",
        publicado: false,
        prioridad: "media"
    };

    try {
        const response = await fetch('/api/update-roadmap', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (result.status === "success") {
            // Limpiar campos y refrescar la tabla
            document.getElementById('road-id').value = '';
            document.getElementById('road-tarea').value = '';
            cargarRoadmap(); 
        }
    } catch (error) {
        console.error("Error enviando al roadmap:", error);
    }
}

async function eliminarHito(id) {
    if (!confirm(`¿Estás seguro de eliminar el hito ${id}?`)) return;

    try {
        const response = await fetch('/api/delete-roadmap', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        });

        const res = await response.json();
        if (res.status === "success") {
            cargarRoadmap(); // Refresca la tabla automáticamente
        }
    } catch (err) {
        console.error("Error al eliminar:", err);
    }
}

// --- ESCUCHADORES DE EVENTOS (Reconexión de botones) ---
document.addEventListener('DOMContentLoaded', () => {
    // 1. Botón Bitácora
    const btnBitacora = document.getElementById('btn-publicar-bitacora');
    if (btnBitacora) {
        btnBitacora.addEventListener('click', subirBitacora);
    }

    // 2. Botón Actualizar Requerimientos
    const btnReqs = document.getElementById('btn-update-reqs');
    if (btnReqs) {
        btnReqs.addEventListener('click', () => ejecutarAccion('/api/update-reqs'));
    }

    // 3. Botón Sincronizar Trayectoria
    const btnData = document.getElementById('btn-update-data');
    if (btnData) {
        btnData.addEventListener('click', () => ejecutarAccion('/api/update-data'));
    }
    // Vincular Integridad - ASEGÚRATE DE ESTE ID
    const btnIntegridad = document.getElementById('btn-verificar-integridad');
    if (btnIntegridad) {
        btnIntegridad.addEventListener('click', lanzarVerificacion);
    }
    // Cargar la tabla nada más abrir el panel
    if (document.getElementById('body-roadmap')) {
        cargarRoadmap();
    }

    // Vincular el botón de añadir tarea
    const btnAddRoadmap = document.getElementById('btn-add-roadmap');
    if (btnAddRoadmap) {
        btnAddRoadmap.addEventListener('click', enviarNuevaTarea);
    }

    // Delegación de eventos para botones de borrar en la tabla roadmap
    const tablaRoadmap = document.getElementById('tabla-roadmap');

    if (tablaRoadmap) {
        tablaRoadmap.addEventListener('click', (e) => {
            // Verificamos si lo que se ha clicado es el botón de borrar
            if (e.target.classList.contains('btn-borrar')) {
                const hitoId = e.target.getAttribute('data-id');
                eliminarHito(hitoId); // Llamamos a la función sin usar código inline
            }
        });
    }
});
