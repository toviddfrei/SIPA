# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automatizado
# Archivo: main.py
# Módulo: SIPAbap (Arranque / Ignición / Guardián)
# Versión: 0.2.5 | Fecha: 06/01/2026
# Autor: Daniel Miñana
# ----------------------------------------------------------
# DESCRIPCIÓN: Orquestador principal de alta disponibilidad.
# Gestiona el ciclo de vida completo: desde la certificación
# temporal (NTP) hasta la transferencia de telemetría a la UI.
# Implementa la "Regla del 30%" para auditoría de rendimiento.
# ==========================================================

# ==========================================================
# PUNTO AUDITORIA FHS-CYBERAUDIT (TEMPORAL EN DESARROLLO)
# ==========================================================
try:
    import sys
    from external.sentinel_fhs_CA import sentinel_v002_fhs_CA as sentinel
    
    # Si ejecutar_auditoria devuelve False, detenemos el proceso
    if not sentinel.sonda.ejecutar_auditoria(sys.argv[0]):
        print("❌ [BLOQUEO FORENSE] La integridad de SIPA ha sido comprometida. Abortando arranque.")
        sys.exit(1) # <--- Aquí es donde se clava el sistema físicamente
        
except ImportError:
    print("⚠️ Sentinel no encontrado. Continuando sin mochila de seguridad.")

# ==========================================================
# IMPORTACIÓN DE MÓDULOS EXTERNOS
# ==========================================================
import time
import socket
import struct
import sys
import os

# ==========================================================
# UBICACIÓN DE LAS RUTAS LOCALES
# ==========================================================
# Aseguramos que el core sea visible independientemente del punto de ejecución
# ¿Qué está haciendo? Mira dónde está este archivo ahora mismo, 
# obtén la dirección completa de su carpeta y añádela a tu lista de búsqueda 
# de bibliotecas.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ==========================================================
# IMPORTACIÓN DE MÓDULOS LOCALES
# ==========================================================
from core.guard.environment_manager import EnvironmentManager
from core.logger.config_loggers import setup_logger
from core.persistence import PersistenceManager
from interface.splash import SipaSplash
from interface.main_dashboard import MainDashboard

# ==========================================================
# CERTIFICACIÓN NTP HORA EXTERNA
# ==========================================================

def get_ntp_time(host="pool.ntp.org"):
    """
    Certificación de soberanía técnica: Obtiene la hora real externa
    para evitar discrepancias en los logs de auditoría de Ubuntu.
    """
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
        t -= 2208988800  # Ajuste de época Unix
        return time.ctime(t)
    except Exception:
        return None

# ==========================================================
# ARRANQUE SIPA
# ==========================================================

def start_engine():
    """
    MOTOR DE IGNICIÓN SIPA:
    1. Certifica tiempo y activa la caja negra (Logs).
    2. Valida la infraestructura física (EnvironmentManager).
    3. Conecta el Kernel de Persistencia (SIPAdel).
    4. Evalúa rendimiento y transfiere el mando al Dashboard.
    """
    # Inicio de telemetría de precisión
    # Iniciado el cronometro para la metríca de duración arranque
    start_perf = time.perf_counter()
    
    # 1. PREPARACIÓN Y TELEMETRÍA INICIAL
    certified_now = get_ntp_time()
    logger, log_messages = setup_logger()
    
    logger.info("==========================================")
    logger.info(f"SIPA BOOT SEQUENCE: Daniel Miñana")
    logger.info(f"CERTIFICACIÓN NTP: {certified_now if certified_now else 'USANDO HORA LOCAL'}")
    logger.info("==========================================")

    # 2. LANZAMIENTO DEL VIGÍA (SPLASH)
    # Iniciamos la interfaz de carga para informar al usuario
    splash = SipaSplash()
    splash.update_status("SIPA: Validando Manifiesto de Seguridad...")
    
    try:
        # --- AUDITORÍA DE INFRAESTRUCTURA ---
        guardian = EnvironmentManager()
        if not guardian.check_all():
            error_msg = "CRÍTICO: Infraestructura física no certificada. Abortando ignición."
            logger.error(error_msg)
            print(f"[!] {error_msg}")
            splash.finalize()
            return

        # 3. IGNICIÓN DEL KERNEL (SIPAdel)
        splash.update_status("SIPA: Conectando Kernel de Persistencia...")
        db = PersistenceManager()
        
        if db.connect():
            # Cálculo de la métrica de arranque (Regla del 30%)
            boot_duration = time.perf_counter() - start_perf
            estado, media = db.registrar_metrica_arranque(boot_duration)
            
            logger.info(f"PERFORMANCE: {estado} | Duración: {boot_duration:.4f}s | Histórico: {media:.4f}s")
            db.register_session(version="0.2.5")
            
            # Feedback visual en el Splash
            splash.update_status(f"Sistema {estado}: Listo en {boot_duration:.2f}s")
            time.sleep(1.2)  # Pausa de cortesía para lectura del estado
        else:
            logger.error("No se pudo establecer conexión con el motor de datos.")
            print("[!] ERROR: Fallo de persistencia en sistema.db")

        # 4. TRANSFERENCIA DE MANDO A LA UI
        # Preparamos los logs acumulados para que el Dashboard los muestre al nacer
        logs_para_panel = list(log_messages)
        
        # El Splash entrega el testigo y finaliza su ciclo de vida
        splash.finalize()
        
        # Instanciamos el Dashboard Principal inyectando la telemetría recolectada
        print(f"[+] Iniciando Panel de Control Integral...")
        app = MainDashboard(logs_inicio=logs_para_panel)
        
        # GIRO DE LLAVE FINAL: Bucle de eventos de la aplicación
        app.run()

    except KeyboardInterrupt:
        print("\n[!] INTERRUPCIÓN MANUAL detectada. Cerrando SIPA de forma segura...")
        if 'splash' in locals(): splash.finalize()
        sys.exit(0)
        
    except Exception as e:
        # Captura de errores de última instancia para evitar cierres "fantasmas"
        error_fatal = f"ERROR NO CONTROLADO EN LA IGNICIÓN: {str(e)}"
        print(f"\n[!!!] {error_fatal}")
        if 'logger' in locals(): logger.critical(error_fatal)
        sys.exit(1)

# ==========================================================
# PUNTO DE ENTRADA ÚNICO
# ==========================================================
if __name__ == "__main__":
    start_engine()