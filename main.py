# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: main.py
# Módulo: SIPAbap (Arranque / Ignición)
# Versión: 0.2.5 | Fecha: 03/01/2026
# Autor: Daniel Miñana
# ----------------------------------------------------------
# DESCRIPCIÓN: Orquestador principal. Implementa telemetría 
# de alta visibilidad y certificación de tiempo externo vía 
# socket NTP (sin dependencias externas).
# ==========================================================

import time
import socket
import struct
from core.guard.environment_manager import EnvironmentManager
from core.logger.config_loggers import setup_logger
from interface.splash import SipaSplash
from interface.main_dashboard import MainDashboard

def get_ntp_time(host="pool.ntp.org"):
    """
    Obtiene la hora oficial vía protocolo NTP usando sockets.
    Certifica la hora sin depender de librerías externas como requests.
    """
    port = 123
    buf = 48
    address = (host, port)
    # Mensaje NTP (protocolo estándar)
    msg = '\x1b' + 47 * '\0'
    
    try:
        # Configuración de socket UDP
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(2.0)
        client.sendto(msg.encode('utf-8'), address)
        data, address = client.recvfrom(buf)
        
        # Desempaquetado del tiempo (segundos desde 1900)
        t = struct.unpack("!12I", data)[10]
        t -= 2208988800 # Ajuste a Unix Epoch (1970)
        
        return time.ctime(t)
    except Exception:
        return None

def start_engine():
    """
    Proceso de Ignición con Auditoría de Tiempo:
    1. Certifica la hora mediante socket NTP.
    2. Activa telemetría en memoria.
    3. Valida infraestructura y mide rendimiento.
    """
    start_perf = time.perf_counter()
    
    # 1. Certificación de tiempo (Ente externo vía NTP)
    certified_now = get_ntp_time()
    
    # 2. Activación del sistema de logs
    logger, log_messages = setup_logger()
    
    logger.info("==========================================")
    logger.info(f"SESIÓN: Daniel Miñana")
    if certified_now:
        logger.info(f"TIEMPO NTP CERTIFICADO: {certified_now}")
    else:
        logger.warning("TIEMPO NO CERTIFICADO: Error de conexión NTP.")
    logger.info("==========================================")

    # --- FASE 1: SPLASH & INFRAESTRUCTURA ---
    splash = SipaSplash()
    splash.update_status("SIPA: Verificando integridad...")
    
    guardian = EnvironmentManager()
    
    if guardian.check_all():
        # Volcado de telemetría a consola para auditoría visual
        for msg in log_messages:
            print(f"[*] TELEMETRÍA: {msg}")

        # --- FASE 2: MÉTRICAS ---
        boot_duration = time.perf_counter() - start_perf
        logger.info(f"Arranque validado en {boot_duration:.4f}s")
        
        splash.update_status(f"Sistema Ready: {boot_duration:.2f}s")
        time.sleep(1.5)
        
        # --- FASE 3: LANZAMIENTO ---
        splash.finalize()
        app = MainDashboard()
        app.run()
    else:
        logger.error("Fallo de infraestructura detectado.")
        splash.finalize()

if __name__ == "__main__":
    start_engine()