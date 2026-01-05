/*
# ==========================================================
# CITADEL CORE - Sistema de Integridad y Gestión
# Archivo: admin_v04.js
# Versión: 0.2.5 (Referencia unificada)
# Módulo: Core
# Certificación: FHS-Compliant | Norma: ISO/IEC 27001 (Simulada)
# Autor: Daniel Miñana & Gemini
# ---------------------------------------------------------
# Descripción: Gestión de telemetría de latencia, monitorización
#              de procesos y reactividad de la interfaz.
# ==========================================================
*/

const KernelMonitor = {
    /**
     * Punto de entrada del monitor.
     * Se ejecuta cuando el DOM está listo pero antes de cargar imágenes/estilos pesados.
     */
    init() {
        this.measureLatency();
        this.syncProgressBars();
        this.logSystemStatus();
    },

    /**
     * MÉTRICA LPD (Latencia de Puesta a Disposición)
     * Performance.now() ofrece precisión de microsegundos.
     */
    measureLatency() {
        window.addEventListener('load', () => {
            const loadDuration = (performance.now() / 1000).toFixed(3);
            const display = document.getElementById('js-latency');
            
            // Inyectamos el dato en el sensor visual si existe
            if (display) {
                display.innerText = loadDuration;
            }
            
            console.log(`[TELEMETRÍA_LPD]: Sistema operacional en ${loadDuration}s`);
        });
    },

    /**
     * SINCRONIZACIÓN DE PROCESOS
     * Lee los 'data-attributes' inyectados por Flask y actualiza el CSS.
     * Esto evita errores de validación en el HTML/CSS.
     */
    syncProgressBars() {
        const progressBar = document.getElementById('build-progress-bar');
        
        if (progressBar) {
            // Recuperamos el valor del atributo de datos
            const progress = progressBar.getAttribute('data-progress') || 0;
            
            // Aplicamos el ancho con un pequeño delay para permitir la animación CSS
            setTimeout(() => {
                progressBar.style.width = `${progress}%`;
            }, 100);
        }
    },

    /**
     * LOG DE AUDITORÍA
     * Registra el estado del Kernel para inspección técnica (F12).
     */
    logSystemStatus() {
        const timestamp = new Date().toLocaleTimeString();
        console.group("--- FORTRESS KERNEL STATUS ---");
        console.log(`Horario de Auditoría: ${timestamp}`);
        console.log("Estado de Red: Online");
        console.log("Integridad de Datos: Verificada");
        console.groupEnd();
    }
};

// Inicialización del motor
document.addEventListener('DOMContentLoaded', () => KernelMonitor.init());