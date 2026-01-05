# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: main.py
# Módulo: SIPAbap (Arranque / Ignición)
# Versión: 0.2.5 | Fecha: 05/01/2026
# Autor: Daniel Miñana
# ----------------------------------------------------------
# DESCRIPCIÓN: Orquestador principal optimizado. 
# Gestiona el ciclo de vida del arranque, la certificación
# por manifiesto y la transferencia de telemetría a la UI.
# ==========================================================

import time
import socket
import struct
import sys 
from core.guard.environment_manager import EnvironmentManager
from core.logger.config_loggers import setup_logger
from core.persistence import PersistenceManager
from interface.splash import SipaSplash
from interface.main_dashboard import MainDashboard

def get_ntp_time(host="pool.ntp.org"):
    """Certificación de hora externa (Soberanía técnica)."""
    port = 123
    buf = 48
    address = (host, port)
    msg = '\x1b' + 47 * '\0'
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(1.5)
        client.sendto(msg.encode('utf-8'), address)
        data, address = client.recvfrom(buf)
        t = struct.unpack("!12I", data)[10]
        t -= 2208988800 
        return time.ctime(t)
    except Exception:
        return None

def start_engine():
    """
    FLUJO DE IGNICIÓN SIPA (v0.2.6):
    1. Certifica tiempo y activa logs.
    2. Ejecuta auditoría por manifiesto (EnvironmentManager).
    3. Persiste rendimiento (SIPAdel).
    4. Lanza Dashboard con visor de logs integrado.
    """
    start_perf = time.perf_counter()
    
    # 1. Preparación de Telemetría
    certified_now = get_ntp_time()
    logger, log_messages = setup_logger()
    
    logger.info("==========================================")
    logger.info(f"SESIÓN: Daniel Miñana")
    logger.info(f"TIEMPO NTP: {certified_now if certified_now else 'LOCAL'}")
    logger.info("==========================================")

    # 2. Splash e Infraestructura
    splash = SipaSplash()
    splash.update_status("SIPA: Validando Manifiesto...")
    
    try:
        guardian = EnvironmentManager()
        if not guardian.check_all():
            logger.error("Infraestructura NO certificada.")
            splash.finalize()
            return

        # 3. Persistencia de Métricas (SIPAdel)
        db = PersistenceManager()
        if db.connect():
            boot_duration = time.perf_counter() - start_perf
            estado, media = db.registrar_metrica_arranque(boot_duration)
            
            logger.info(f"RENDIMIENTO: {estado} | Actual: {boot_duration:.4f}s | Media: {media:.4f}s")
            db.register_session(version="0.2.6")
            
            # --- DETALLE: VISIBILIDAD DEL SPLASH ---
            splash.update_status(f"Sistema {estado}: {boot_duration:.2f}s")
            time.sleep(1.5) # Pausa necesaria para auditar visualmente el splash

        # --- VOLCADO A CONSOLA Y PREPARACIÓN DE UI ---
        # Creamos una copia de los logs para la interfaz antes de limpiar o cerrar
        logs_para_panel = list(log_messages)
        
        for msg in log_messages:
            print(f"[*] TELEMETRÍA: {msg}")

        # 4. Lanzamiento de Dashboard
        splash.finalize()
        
        # Pasamos los logs recolectados al constructor del Panel
        app = MainDashboard(logs_inicio=logs_para_panel)
        app.run()

    except KeyboardInterrupt:
        print("\n[!] INTERRUPCIÓN MANUAL: Cerrando SIPA de forma segura...")
        if 'splash' in locals(): splash.finalize()
        sys.exit(0)
    except Exception as e:
        print(f"[!] ERROR NO CONTROLADO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_engine()