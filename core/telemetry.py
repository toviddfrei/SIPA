# ==========================================================
# CITADEL CORE - Sistema de Integridad y Gestión
# Archivo: telemetry.py
# Versión: 0.2.5 (Referencia unificada)
# Módulo: Core
# Certificación: FHS-Compliant | Norma: ISO/IEC 27001 (Simulada)
# Autor: Daniel Miñana & Gemini
# ---------------------------------------------------------
# Descripción: Telemetría y recopilación de datos anónimos
# ==========================================================

import logging
import os

# Aseguramos que el directorio de logs exista en la raíz
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "citadel_main.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_event(message, level="info"):
    """Registra un evento en el búnker."""
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    print(f"[*] Telemetry: {message}")

if __name__ == "__main__":
    log_event("Telemetry system initialized - All systems nominal.")