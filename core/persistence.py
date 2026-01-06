# ==========================================================
# PROYECTO SIPA - Sistema de Inteligencia de Perfil Automático
# Archivo: persistence.py
# Módulo: SIPAdel (Kernel / Persistencia)
# Versión: 0.2.5 | Fecha: 06/01/2026
# Autor: Daniel Miñana & Gemini
# ----------------------------------------------------------
# DESCRIPCIÓN: Gestión de la Capa de Persistencia (SQLite).
# Centraliza logs, sesiones y la "Carretera" (Roadmap)
# bajo normativa de seguridad y auditoría.
# "Buscamos la excelencia en la integridad de los datos".
# ==========================================================

import sqlite3
import os
import json
import sys
from datetime import datetime

# ==========================================================
# BLOQUE DE RUTAS: SINCRONIZACIÓN CON CONFIG.PY (NORMA SIPA)
# ==========================================================
try:
    # Intentamos la importación directa desde el núcleo
    from core.config import DB_PATH
except ImportError:
    # Salvaguarda para ejecución desde diferentes puntos en Ubuntu
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)
    from core.config import DB_PATH

class PersistenceManager:
    """
    Motor de persistencia de SIPA. Gestiona el ciclo de vida
    de los datos y la inteligencia de rendimiento (SIPAdel).
    """
    def __init__(self):
        # La norma: DB_PATH viene de config.py (Path object)
        self.db_path = str(DB_PATH)
        self._conn = None
        self._cursor = None 

    def connect(self):
        """Establece conexión y asegura la integridad de tablas."""
        try:
            # PASO 1: Asegurar que el directorio existe (Ubuntu Permission Check)
            db_dir = os.path.dirname(self.db_path)
            if not os.path.exists(db_dir):
                print(f"[DEBUG] Creando directorio centralizado: {db_dir}")
                os.makedirs(db_dir, exist_ok=True)
            
            # PASO 2: Conexión física
            print(f"[DEBUG] SIPAdel intentando conectar a: {self.db_path}")
            self._conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
            self._cursor = self._conn.cursor()
            
            # PASO 3: Recreación de esquema si no existe
            self.create_tables()
            return True
        except Exception as e:
            # Captura TODO para evitar cierre inmediato del Splash
            print(f"\n[-] ERROR CRÍTICO EN EL KERNEL DE PERSISTENCIA: {e}")
            print(f"[-] RUTA SOLICITADA POR CONFIG: {self.db_path}\n")
            return False

    def create_tables(self):
        """Crea la estructura de tablas para el ecosistema SIPA v0.2.5."""
        # 1. Logs de Telemetría (Caja Negra)
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                session_id INTEGER,
                level TEXT,
                name TEXT,
                message TEXT,
                context_json TEXT
            )
        """)
        
        # 2. Historial de Sesiones
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                version TEXT,
                status TEXT
            )
        """)

        # 3. Métricas de Rendimiento (Regla del 30%)
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS metricas_arranque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                duracion REAL,
                estado TEXT
            )
        """)

        # 4. Roadmap / Carretera Estratégica (Evolución N1/N2)
        # Incluye 'vinculo_archivo' para la integración con Curator/Knowledge
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS roadmap (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,          -- Fecha de creación del registro
                fecha_objetivo TEXT,     -- Fecha del hito (Pasado o Futuro)
                rango_superior TEXT,     -- Nivel 1 (Contexto)
                etiqueta_sub TEXT,       -- Nivel 2 (Acción)
                tarea TEXT,              -- Título/Descripción corta
                nota_extendida TEXT,     -- Contenido largo / Daily
                estado TEXT,             -- PENDIENTE, COMPLETADO
                vinculo_archivo TEXT     -- Relación con data/knowledge
            )
        """)
        self._conn.commit()

    # ----------------------------------------------------------------------
    # SISTEMA DE ROADMAP (Lógica de Carretera)
    # ----------------------------------------------------------------------

    def agregar_hito_roadmap(self, fecha_obj, n1, n2, tarea, nota="", archivo=""):
        """Inserta un nuevo hito con jerarquía de etiquetas."""
        try:
            if not self.is_connected(): self.connect()
            ts_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = """INSERT INTO roadmap 
                     (timestamp, fecha_objetivo, rango_superior, etiqueta_sub, tarea, nota_extendida, estado, vinculo_archivo) 
                     VALUES (?, ?, ?, ?, ?, ?, 'PENDIENTE', ?)"""
            self._cursor.execute(sql, (ts_creacion, fecha_obj, n1, n2, tarea, nota, archivo))
            self._conn.commit()
            return True
        except Exception as e:
            print(f"[-] Error al insertar hito: {e}")
            return False

    def obtener_roadmap_filtrado(self, n1="ALL", n2="ALL"):
        """Consulta profesional con filtros dinámicos para el Dashboard e IA."""
        try:
            if not self.is_connected(): self.connect()
            query = "SELECT id, fecha_objetivo, rango_superior, etiqueta_sub, tarea, vinculo_archivo FROM roadmap WHERE 1=1"
            params = []

            if n1 != "ALL":
                query += " AND rango_superior = ?"
                params.append(n1)
            if n2 != "ALL":
                query += " AND etiqueta_sub = ?"
                params.append(n2)

            query += " ORDER BY fecha_objetivo ASC"
            self._cursor.execute(query, params)
            return self._cursor.fetchall()
        except Exception:
            return []

    def obtener_detalle_roadmap(self, item_id):
        """Recupera la anotación extendida para el visor lateral."""
        try:
            if not self.is_connected(): self.connect()
            self._cursor.execute("SELECT nota_extendida FROM roadmap WHERE id = ?", (item_id,))
            res = self._cursor.fetchone()
            return res[0] if res else "Sin detalles registrados."
        except Exception:
            return "Error al recuperar detalles."

    # ----------------------------------------------------------------------
    # TELEMETRÍA Y MÉTRICAS (Regla del 30%)
    # ----------------------------------------------------------------------

    def registrar_metrica_arranque(self, duracion_actual):
        """Aplica la Regla del 30% de Daniel Miñana."""
        try:
            if not self.is_connected(): self.connect()
            
            # Calculamos media de las últimas 20 sesiones
            query_media = "SELECT AVG(duracion) FROM (SELECT duracion FROM metricas_arranque ORDER BY id DESC LIMIT 20)"
            self._cursor.execute(query_media)
            res = self._cursor.fetchone()[0]
            media_historica = res if res is not None else duracion_actual

            umbral_alerta = media_historica * 1.30
            estado = "OPTIMO" if duracion_actual <= umbral_alerta else "IRREGULAR"
            
            self._cursor.execute("INSERT INTO metricas_arranque (timestamp, duracion, estado) VALUES (?, ?, ?)", 
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), duracion_actual, estado))
            self._conn.commit()
            return estado, media_historica
        except Exception:
            return "ERROR", 0

    def obtener_metricas_recientes(self, limite=10):
        try:
            if not self.is_connected(): self.connect()
            self._cursor.execute("SELECT timestamp, duracion, estado FROM metricas_arranque ORDER BY id DESC LIMIT ?", (limite,))
            return self._cursor.fetchall()
        except Exception:
            return []

    # ----------------------------------------------------------------------
    # GESTIÓN DE LOGS Y SESIONES
    # ----------------------------------------------------------------------

    def insert_log(self, record_dict):
        """Inserta logs en la Caja Negra (app_logs)."""
        try:
            if not self.is_connected(): self.connect()
            sql = "INSERT INTO app_logs (timestamp, session_id, level, name, message, context_json) VALUES (?, ?, ?, ?, ?, ?)"
            values = (
                record_dict.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                record_dict.get('session_id', 0),
                record_dict.get('level', 'INFO'),
                record_dict.get('name', 'root'),
                record_dict.get('message', ''),
                record_dict.get('context_json', '{}')
            )
            self._cursor.execute(sql, values)
            self._conn.commit()
        except Exception:
            pass

    def register_session(self, version="0.2.5"):
        try:
            if not self.is_connected(): self.connect()
            sql = "INSERT INTO sessions (start_time, version, status) VALUES (datetime('now','localtime'), ?, 'ACTIVE')"
            self._cursor.execute(sql, (version,))
            self._conn.commit()
            return self._cursor.lastrowid
        except Exception:
            return 0

    def is_connected(self):
        try:
            return self._conn is not None and self._conn.execute("SELECT 1")
        except: return False

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

# Firmado: Daniel Miñana & SIPA AI Assistant
# "La excelencia es el resultado de la integridad en cada bit".