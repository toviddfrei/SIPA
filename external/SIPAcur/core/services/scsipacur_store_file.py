# ==========================================================
# PROYECTO SIPA - Sistema identificación personal autorizada
# Archivo: scsipacur_store_file.py
# Módulo: Servicio Interno SIPAcur (SIPAstore)
# Versión: 1.0.0 | Fecha: 23/05/2026
# ----------------------------------------------------------
# OBJETIVO: Motor de datos, Logs de Trazabilidad e IA local.
# ==========================================================

import os
import json
import getpass
from datetime import datetime

class SIPA_Store_Service:
    def __init__(self):
        # 1. Identidad propia del servicio dentro de SIPAcur
        self.service_name = "SIPAcur-store-file"
        self.status = "ACTIVE"
        self.start_time = datetime.now()
        
        # 2. Entorno y Rutas del Santuario de Datos
        self.user_name = getpass.getuser()
        self.base_path = f"/home/{self.user_name}/SIPA"
        
        # Logs de ciclo de vida inmutable (Nota 1 de la Bitácora)
        self.path_lifecycle_log = os.path.join(self.base_path, "external/SIPAcur/logs/sipa_lifecycle.log")
        os.makedirs(os.path.dirname(self.path_lifecycle_log), exist_ok=True)
        
        # Latido inicial de presentación
        self._registrar_hito_inicial()

    def obtener_salud_servicio(self):
        """Devuelve el estado y uptime exacto para la pestaña INBOX/INICIO de SIPAcur."""
        tiempo_activo = datetime.now() - self.start_time
        return {
            "servicio": self.service_name,
            "estado": self.status,
            "operario": self.user_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "uptime_segundos": int(tiempo_activo.total_seconds())
        }

    def _registrar_hito_inicial(self):
        """Inyecta el nacimiento del servicio en la bitácora inmutable."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje = f"[{timestamp}] [{self.service_name.upper()}_INIT] Servicio de almacenamiento e IA activo de forma estanca.\n"
        try:
            with open(self.path_lifecycle_log, "a", encoding="utf-8") as f:
                f.write(mensaje)
            print(f"🟢 {self.service_name}: Aquí estoy y estoy activo.")
        except Exception as e:
            print(f"❌ Error en bitácora de {self.service_name}: {e}")

if __name__ == "__main__":
    # Prueba autónoma en terminal
    store = SIPA_Store_Service()
    print(json.dumps(store.obtener_salud_servicio(), indent=4, ensure_ascii=False))