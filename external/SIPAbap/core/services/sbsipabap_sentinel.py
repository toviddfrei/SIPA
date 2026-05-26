# =====================================================================
# MÓDULO: sbsipabap_sentinel.py (v0.2.5 - Core Infr)
# UBICACIÓN: /home/toviddfrei/SIPA/external/SIPAbap/core/services/
# DESCRIPCIÓN: Absorción del motor forense SENTINEL_fhs-CA (v0.0.2.1).
#              Custodia integridad SHA-256, análisis AST y telemetría RAM/CPU.
# AUTOR: Daniel Miñana Montero & Gemini
# =====================================================================

import os
import sys
import ast
import logging
import psutil
import time
import hashlib
from datetime import datetime
from threading import Thread

# Acoplamiento a tu Única Fuente de Verdad (SSoT)
from core.config import (
    BASE_DIR,
    DIR_DATA,
    NAME_LOGGER_ESTRUCTURA
)

# Centralización del Sello de Seguridad en la zona de datos unificada
SELLO_FILE = DIR_DATA / ".sipa_secret"

# Nos enganchamos a tus manejadores en memoria (ListHandler / DatabaseHandler)
logger_sipa = logging.getLogger(NAME_LOGGER_ESTRUCTURA)

class CyberAuditForense:
    """
    Motor de auditoría con logs específicos para depuración de arranque.
    Integrado en el flujo unificado de SIPAbap.
    """

    def __init__(self):
        """Inicializa el sistema forense y captura el PID del proceso raíz."""
        self.root_pid = os.getpid()
        self.proceso_raiz = psutil.Process(self.root_pid)
        self.visto = set()
        
        # Logs de inicialización integrados
        self.log_evento("INIT", f"Instanciando CyberAuditForense en ecosistema unificado. PID: {self.root_pid}")
        self.log_evento("PATH", f"VRAM BASE_DIR activa en: {BASE_DIR}")
        self.log_evento("PATH", f"SELLO_FILE custodiado en: {SELLO_FILE}")

    def log_evento(self, categoria, mensaje):
        """Salida dual (Consola SIPA/Búnker de logs estructurales)."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        linea = f"Estado: {categoria} | {mensaje} | Módulo: FHS-CyberAudit | Timestamp: {ts}"
        
        # En lugar de logging genérico, alimenta tu ListHandler y tu log maestro
        logger_sipa.info(linea)
        print(f"📡 {linea}")

    def verificar_integridad_sha256(self, target):
        """
        BLOQUE 1: SEGURIDAD.
        Verifica el hash de sipa.py y gestiona el sello .sipa_secret.
        """
        self.log_evento("CHECK_INTEGRIDAD", f"Iniciando verificación forense para: {target}")
        
        sha256_hash = hashlib.sha256()
        try:
            with open(target, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            current_hash = sha256_hash.hexdigest()
            self.log_evento("HASH_CALCULADO", f"SHA256: {current_hash}")
        except Exception as e:
            self.log_evento("ERROR_CRÍTICO", f"No se pudo leer el archivo objetivo: {e}")
            return False

        # Verificamos existencia del sello
        if not os.path.exists(SELLO_FILE):
            self.log_evento("SEGURIDAD", f"Sello no encontrado. Generando ancla: {SELLO_FILE}")
            try:
                with open(SELLO_FILE, "w") as f:
                    f.write(current_hash)
                self.log_evento("SISTEMA", "¡ÉXITO! Sello .sipa_secret generado correctamente en búnker de datos.")
                return True
            except Exception as e:
                self.log_evento("ERROR_CRÍTICO", f"No se pudo escribir el sello: {e}")
                return False

        # Si el sello existe, comparamos firmas criptográficas
        try:
            with open(SELLO_FILE, "r") as f:
                stored_hash = f.read().strip()
            
            self.log_evento("COMPARACIÓN", f"Hash actual vs guardado en {SELLO_FILE}")
            
            if current_hash == stored_hash:
                self.log_evento("INTEGRIDAD", "OK - El código coincide con el sello original.")
                return True
            else:
                self.log_evento("ALERTA_CRÍTICA", "¡FIRMA NO COINCIDE! Código modificado o corrupción detectada.")
                return False
        except Exception as e:
            self.log_evento("ERROR_CRÍTICO", f"Error leyendo el sello existente: {e}")
            return False

    def auditar_contenido_fichero(self, target):
        """BLOQUE 1: EXCELENCIA. Análisis AST profundo y métricas de salud lógica."""
        self.log_evento("AST_START", f"Analizando estructura lógica de: {target}")
        try:
            with open(target, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            
            nodos_doc, total_nodos = 0, 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    total_nodos += 1
                    if ast.get_docstring(node):
                        nodos_doc += 1
            
            densidad = (nodos_doc / total_nodos) * 100 if total_nodos > 0 else 0
            self.log_evento("SALUD_LÓGICA", f"Densidad Docstrings: {densidad:.2f}% ({nodos_doc}/{total_nodos})")
        except Exception as e:
            self.log_evento("ERROR_AST", f"Fallo en inspección del árbol sintáctico: {e}")

    def monitor_recursos_continuo(self):
        """BLOQUE 2: MONITOREO. Registro asíncrono de salud de recursos."""
        self.log_evento("SNIFFER", "Hilo de monitorización dinámico de telemetría iniciado.")
        while True:
            try:
                cpu = self.proceso_raiz.cpu_percent()
                mem = self.proceso_raiz.memory_info().rss / (1024 * 1024)
                self.log_evento("HEARTBEAT", f"Salud Proceso -> CPU: {cpu}% | RAM: {mem:.2f}MB")
                time.sleep(10)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.log_evento("SISTEMA", "Proceso raíz finalizado o inaccesible. Cerrando sniffer.")
                break

    def ejecutar_auditoria(self, target):
        """Coordinador del ciclo de vida y arranque seguro de Sentinel."""
        self.log_evento("AUDIT_START", "Iniciando secuencia completa de ciber-auditoría...")
        
        # 1. Validación estricta de Integridad
        if not self.verificar_integridad_sha256(target):
            self.log_evento("STOP", "Bloqueo preventivo de seguridad por fallo de integridad.")
            return False
        
        # 2. Análisis estático de código
        self.auditar_contenido_fichero(target)

        # 3. Ignición de Telemetría en segundo plano
        Thread(target=self.monitor_recursos_continuo, daemon=True).start()
        
        self.log_evento("SIPA_READY", "Sentinel v0.2.5 operativa, acoplada a RAM y vigilando.")
        return True

# Sonda global lista para ser invocada por el lanzador
sonda = CyberAuditForense()