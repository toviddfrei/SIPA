"""
MÓDULO: SENTINEL_fhs-CA (v0.0.2.1)
DESCRIPCIÓN: Sistema de auditoría forense con logs de alta intensidad.
             Implementa integridad SHA-256 (archivo oculto) y análisis AST.
AUTOR: Daniel Miñana & Gemini
FECHA: 2026-01-07
"""

import os
import sys
import ast
import logging
import psutil
import time
import hashlib
from datetime import datetime
from threading import Thread

# === CONFIGURACIÓN DE RUTAS Y CONSTANTES ===
# Forzamos la detección de la ruta absoluta para evitar fallos de importación
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
FICHA_DIR = os.path.join(BASE_DIR, "ficha_tecnica")

# Garantizamos estructura de directorios
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(FICHA_DIR, exist_ok=True)

# Centralización de Archivos Críticos
LOG_FILE = os.path.join(LOG_DIR, "SIPA_Audit_Master.log")
SELLO_FILE = os.path.join(FICHA_DIR, ".sipa_secret") 

# Configuración de Logging con nivel INFO para máxima visibilidad
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s | [%(levelname)s] | %(message)s',
    filemode='a'
)

class CyberAuditForense:
    """
    Motor de auditoría con logs específicos para depuración de arranque.
    """

    def __init__(self):
        """Inicializa el sistema y registra el estado del entorno."""
        self.root_pid = os.getpid()
        self.proceso_raiz = psutil.Process(self.root_pid)
        self.visto = set()
        
        # Log de inicialización
        self.log_evento("INIT", f"Instanciando CyberAuditForense. PID: {self.root_pid}")
        self.log_evento("PATH", f"BASE_DIR detectado en: {BASE_DIR}")
        self.log_evento("PATH", f"SELLO_FILE configurado en: {SELLO_FILE}")

    def log_evento(self, categoria, mensaje):
        """Salida dual (Consola/Fichero) con formato de auditoría."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        linea = f"Estado: {categoria} | {mensaje} | Módulo: FHS-CyberAudit | Timestamp: {ts}"
        logging.info(linea)
        print(f"📡 {linea}")

    def verificar_integridad_sha256(self, target):
        """
        BLOQUE 1: SEGURIDAD.
        Verifica el hash del archivo y gestiona el sello .sipa_secret.
        """
        self.log_evento("CHECK_INTEGRIDAD", f"Iniciando verificación para: {target}")
        
        sha256_hash = hashlib.sha256()
        try:
            with open(target, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            current_hash = sha256_hash.hexdigest()
            self.log_evento("HASH_CALCULADO", f"SHA256: {current_hash}")
        except Exception as e:
            self.log_evento("ERROR_CRÍTICO", f"No se pudo leer el archivo target: {e}")
            return False

        # Verificamos existencia del sello
        if not os.path.exists(SELLO_FILE):
            self.log_evento("SEGURIDAD", f"Sello no encontrado. Intentando crear: {SELLO_FILE}")
            try:
                with open(SELLO_FILE, "w") as f:
                    f.write(current_hash)
                self.log_evento("SISTEMA", "¡ÉXITO! Sello .sipa_secret generado correctamente.")
                return True
            except Exception as e:
                self.log_evento("ERROR_CRÍTICO", f"No se pudo escribir el sello: {e}")
                return False

        # Si el sello existe, comparamos
        try:
            with open(SELLO_FILE, "r") as f:
                stored_hash = f.read().strip()
            
            self.log_evento("COMPARACIÓN", f"Hash actual vs guardado en {SELLO_FILE}")
            
            if current_hash == stored_hash:
                self.log_evento("INTEGRIDAD", "OK - El código coincide con el sello original.")
                return True
            else:
                self.log_evento("ALERTA_CRÍTICA", "¡FIRMA NO COINCIDE! Posible manipulación.")
                return False
        except Exception as e:
            self.log_evento("ERROR_CRÍTICO", f"Error leyendo el sello existente: {e}")
            return False

    def auditar_contenido_fichero(self, target):
        """BLOQUE 1: EXCELENCIA. Análisis AST profundo."""
        self.log_evento("AST_START", f"Analizando estructura de: {target}")
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
            self.log_evento("ERROR_AST", f"Fallo en inspección: {e}")

    def monitor_recursos_continuo(self):
        """BLOQUE 2: MONITOREO. Registro de telemetría constante."""
        self.log_evento("SNIFFER", "Hilo de monitorización dinámico iniciado.")
        while True:
            try:
                cpu = self.proceso_raiz.cpu_percent()
                mem = self.proceso_raiz.memory_info().rss / (1024 * 1024)
                # Registro cada 10 segundos para no saturar pero mantener rastro
                self.log_evento("HEARTBEAT", f"Salud Proceso -> CPU: {cpu}% | RAM: {mem:.2f}MB")
                time.sleep(10)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.log_evento("SISTEMA", "Proceso terminado. Cerrando monitor.")
                break

    def ejecutar_auditoria(self, target):
        """Coordinador del ciclo de vida de Sentinel."""
        self.log_evento("AUDIT_START", "Iniciando secuencia completa de auditoría...")
        
        # 1. Integridad SHA-256
        if not self.verificar_integridad_sha256(target):
            self.log_evento("STOP", "Bloqueo por fallo de integridad.")
            return False
        
        # 2. Análisis AST
        self.auditar_contenido_fichero(target)

        # 3. Lanzamiento de Telemetría
        Thread(target=self.monitor_recursos_continuo, daemon=True).start()
        
        self.log_evento("SIPA_READY", "Sentinel v0.0.2.1 operativa y vigilando.")
        return True

# --- BOOTSTRAP ---
sonda = CyberAuditForense()

if __name__ == "__main__":
    # Si se ejecuta este script solo, se audita a sí mismo
    objetivo = sys.argv[1] if len(sys.argv) > 1 else sys.argv[0]
    sonda.ejecutar_auditoria(objetivo)