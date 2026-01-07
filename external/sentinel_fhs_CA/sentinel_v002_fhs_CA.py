"""
MÓDULO: SENTINEL_fhs-CA (v0.0.2)
DESCRIPCIÓN: Sistema de auditoría forense y monitorización de integridad.
             Actúa como 'mochila' de seguridad para el PROYECTO SIPA.
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

# === CONFIGURACIÓN DE ESTRUCTURA PROFESIONAL ===
# Definimos las rutas relativas para garantizar la portabilidad del módulo.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
FICHA_DIR = os.path.join(BASE_DIR, "ficha_tecnica")

# Aseguramos la existencia del ecosistema de archivos del módulo
for d in [LOG_DIR, FICHA_DIR]:
    os.makedirs(d, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "SIPA_Audit_Master.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    filemode='a'
)

class CyberAuditForense:
    """
    Clase principal de Sentinel encargada de la monitorización dual:
    1. Estática (Análisis de código y seguridad SHA-256).
    2. Dinámica (Uso de recursos y telemetría en tiempo real).
    """

    def __init__(self):
        """Inicializa el rastreo obteniendo la identidad del proceso raíz."""
        self.root_pid = os.getpid()
        self.proceso_raiz = psutil.Process(self.root_pid)
        self.visto = set()
        self.secret_file = os.path.join(BASE_DIR, ".sipa_secret")
        self.log_evento("SISTEMA", f"Sentinel v0.0.2 activo sobre PID {self.root_pid}")

    def log_evento(self, categoria, mensaje):
        """
        Estandariza la salida de eventos para su posterior lectura por el panel SIPA.
        
        Args:
            categoria (str): Etiqueta del evento (SISTEMA, SEGURIDAD, ALERTA).
            mensaje (str): Descripción detallada del suceso.
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        linea = f"Estado: {categoria} | {mensaje} | Módulo: FHS-CyberAudit | Timestamp: {ts}"
        logging.info(linea)
        print(f"📡 {linea}")

    def verificar_integridad_sha256(self, target):
        """
        BLOQUE 1 - SEGURIDAD: Implementa el 'Sello de Veracidad'.
        Utiliza el algoritmo SHA-256 para detectar cualquier alteración en el código.
        
        Pedagogía: Se lee en bloques de 4KB para evitar picos de memoria al 
        procesar archivos grandes (eficiencia de buffer).
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(target, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            current_hash = sha256_hash.hexdigest()
        except Exception as e:
            self.log_evento("ERROR_CRÍTICO", f"No se pudo generar hash: {e}")
            return False

        print(f"DEBUG: Buscando secreto en: {self.secret_file}")
        # Lógica de persistencia del secreto: Si no existe, se crea (Primer arranque)
        if not os.path.exists(self.secret_file):
            with open(self.secret_file, "w") as f:
                f.write(current_hash)
            self.log_evento("SISTEMA", "Sello inicial generado. Integridad blindada.")
            return True

        with open(self.secret_file, "r") as f:
            stored_hash = f.read().strip()

        return current_hash == stored_hash

    def auditar_contenido_fichero(self, target):
        """
        BLOQUE 1 - EXCELENCIA: Análisis AST (Abstract Syntax Tree).
        Analiza la estructura del código sin ejecutarlo para medir su calidad documental.
        
        Valor: Asegura que el aprendizaje automático de SIPA tenga fuentes 
        bien documentadas (docstrings).
        """
        try:
            with open(target, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            
            nodos_doc, total_nodos, alertas_logica = 0, 0, 0

            for node in ast.walk(tree):
                # Verificamos si las estructuras clave tienen documentación
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    total_nodos += 1
                    if ast.get_docstring(node):
                        nodos_doc += 1
                    else:
                        nombre = getattr(node, 'name', 'Raíz')
                        self.log_evento("AVISO_DOC", f"Código huérfano de docstring en: {nombre}")

            densidad = (nodos_doc / total_nodos) * 100 if total_nodos > 0 else 0
            self.log_evento("SALUD_LÓGICA", f"Densidad Docstrings: {densidad:.2f}%")
            
        except Exception as e:
            self.log_evento("ERROR_AUDITORÍA", f"Fallo en motor AST: {str(e)}")

    def monitor_recursos_continuo(self):
        """
        BLOQUE 2 - MONITOREO: Hilo de telemetría dinámica.
        Rastrea el consumo de CPU y RAM de forma persistente.
        """
        while True:
            try:
                hijos = self.proceso_raiz.children(recursive=True)
                for h in [self.proceso_raiz] + hijos:
                    with h.oneshot():
                        pid, cpu, mem = h.pid, h.cpu_percent(), h.memory_info().rss / (1024 * 1024)
                        if cpu > 0.1: # Filtro de ruido para el log
                            self.log_evento("CONSUMO", f"PID: {pid} | CPU: {cpu}% | RAM: {mem:.2f}MB")
                time.sleep(2) # Pausa pedagógica para no sobrecargar el sistema
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

    def ejecutar_auditoria(self, target):
        """Coordina las fases de la mochila según el checklist."""
        # Fase 1: Integridad (Prioridad máxima)
        if not self.verificar_integridad_sha256(target):
            self.log_evento("ALERTA_CRÍTICA", "¡INTEGRIDAD VIOLADA! El código ha cambiado.")
            return False
        
        self.log_evento("INTEGRIDAD", "OK - Sello verificado.")

        # Fase 2: Auditoría de Excelencia
        self.auditar_contenido_fichero(target)

        # Fase 3: Lanzamiento de Monitorización en segundo plano
        Thread(target=self.monitor_recursos_continuo, daemon=True).start()
        
        self.log_evento("SIPA_READY", "Sentinel operativo en modo vigilancia.")
        return True

# --- PUNTO DE ENTRADA (BOOTSTRAP) ---
sonda = CyberAuditForense()

if __name__ == "__main__":
    # Permite ejecución manual: python sentinel_v002_fhs_CA.py mi_script.py
    objetivo = sys.argv[1] if len(sys.argv) > 1 else sys.argv[0]
    sonda.ejecutar_auditoria(objetivo)