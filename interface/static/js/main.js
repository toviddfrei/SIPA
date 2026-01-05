/*
# ==========================================================
# CITADEL CORE - Sistema de Integridad y Gestión
# Archivo: main.js
# Versión: 0.2.5 (Referencia unificada)
# Módulo: Core
# Certificación: FHS-Compliant | Norma: ISO/IEC 27001 (Simulada)
# Autor: Daniel Miñana & Gemini
# ---------------------------------------------------------
# Descripción: Gestión de UI y Temas Adaptativos
#              Implementa lógica no invasiva para la experiencia de usuario (UX).
# ==========================================================
*/

// 1. Gestión del Tema (Día/Noche) según horario local
function aplicarTemaAutomatico() {
    const hora = new Date().getHours();
    const htmlElement = document.documentElement; // Usamos el root para evitar parpadeos
    
    // De 8:00 a 20:00 -> Modo Claro (Pastel)
    // De 20:00 a 7:59 -> Modo Noche
    if (hora >= 8 && hora < 20) {
        htmlElement.setAttribute('data-theme', 'light');
    } else {
        htmlElement.setAttribute('data-theme', 'night');
    }
}

// 2. Función para cerrar el banner (Tu código mejorado)
function cerrarBanner() {
    const banner = document.getElementById('banner-notificacion');
    if (banner) {
        banner.style.opacity = '0'; // Efecto visual suave
        setTimeout(() => {
            banner.style.display = 'none';
        }, 500); 
        sessionStorage.setItem('banner-cerrado', 'true');
    }
}

// 3. Inicialización al cargar el DOM
document.addEventListener('DOMContentLoaded', () => {
    aplicarTemaAutomatico();

    // Verificamos el banner
    if (sessionStorage.getItem('banner-cerrado') === 'true') {
        const banner = document.getElementById('banner-notificacion');
        if (banner) banner.style.display = 'none';
    }

    // --- NUEVO: Asignación segura del botón ---
    const btnCerrar = document.getElementById('boton-cerrar-banner');
    if (btnCerrar) {
        btnCerrar.addEventListener('click', cerrarBanner);
    }
});
